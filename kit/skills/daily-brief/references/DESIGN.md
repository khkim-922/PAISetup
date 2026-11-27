# 일일 보고의 설계

일일 보고 스킬의 코드를 고치는 사람이 읽는다. 무엇이 어떻게 도는지 — 조각의 지도, 사람이 일으키는 흐름과 정한 시각에 사람 없이 도는 시계 ·
맡긴 일의 실행, 다른 스킬과 창이 기대는 약속, 하지 않는 것 — 을 이 글 하나에서 읽게 한다. 쓰는 법은 `SKILL.md` 가, 보고 글의 꼴은 `lane.md` 「보고 글의 꼴」이, 명령마다 부르는 꼴 · 내는
것 · 종료 값은 그 스크립트의 머리말이 든다.

## 무엇을 하나 — 사람이 보는 것

비서 모델이 메일과 일정을 읽어 지금 보실 것을 고르고 까닭을 붙인 **보고 글**(마크다운)을 쓴다. 이 스킬의 코드는 그 글을 **보고 창**(HTML 한
장)으로 지어 사용자의 로그인 Edge 새 탭에 띄우고, 창에서 누르신 것을 거둬 제자리에 옮기고, 다음 보고가 그것을 이어 읽게 한다.

```
모델이 쓴 보고 글 ─▶ 마무리 ─▶ 보고 창 + 남는 보고 글 ─▶ 사람이 누른다 ─▶ 창 곁의 손이 바로 하거나, 다음 보고 · 시계 판이 거둔다 ─▶ 다음 보고
```

창에서 사람이 보는 것은 이렇다.

- **머리** — 언제 지은 보고인가, 비서가 사람 없이 사내 로그인을 새로 하고 지은 보고면 그 사실과 하실 일 한 줄, 「비서에게 부탁하기」 칸(VS Code 의
  Claude Code 가 있는 PC), 맡길 일이 있으면 「바로 맡길 일」 막대
- **사람별** — 나를 기다리는 분 · 내가 답을 기다리는 분과 그 줄로 가는 링크
- **절과 카드** — 모델이 그날 형편대로 세운 절. 메일 줄은 그 메일을 웹메일에서 여는 링크이고, 할 일의 줄마다 「끝났음 · 내일 다시 · 안 올려도
  됨」 단추, 카드마다 그 건에서 맡길 일(「일정 넣기」 · 회의실 잡기 · 답장 따위)과 표시 칸 · 단추가 선다
- **끝의 「보고 맞추기」** — 보고 시각 · 「자리 밖에서 보기」 · 보고에서 빼는 것 · 내일 다시 볼 것
- 「자리 밖에서 보기」를 켜셨으면 사람 없이 지은 보고가 휴대폰 너비의 **메일 한 장**으로도 온다(보내는 것은 시계)

사람이 부르지 않아도 도는 일이 둘 더 있다. 하나는 **정한 시각의 보고** — 사용자가 시각을 걸어 두셨으면 시계(`unattended/`)가 그 시각마다 사내
세션을 보고 · 필요하면 로그인하고 · 메일함 스캔에 한 판을 청한 뒤 보고를 짓는 claude 를 사람 없이 띄운다. 그 보고가 창을 띄워 두고 사용자는 오셔서
본다. 다른 하나는 **맡긴 일** — 창에서 누른 일(회의실 잡기 · 답장 써 두기 따위)을 뒤에서 claude 한 번으로 하고 일마다의 끝을 창에 돌려준다. 두 일은
메일에서 온 글을 품은 창의 손(`scripts/`)과 울타리가 달라 `unattended/` 에 산다.

판단은 모델이, 정해진 값과 셈은 코드가 든다. 무엇을 올리나 · 어느 일인가 · 무엇을 맡길까 · 누가 기다리나는 모델이 보고 글에 쓰고, 코드는 그
판단을 다시 하지 않는다. 일정 손이 낸 열쇠 · 지난 보고의 기록 절 · 시각표와 보고 맞춤처럼 이미 정해진 값은 코드가 그 원본에서 들고
온다 — 모델이 옮겨 적게 하면 한 번 빠뜨리거나 한 글자 틀리는 날 사용자가 정한 것이 사라지거나 창이 거짓을 말한다. 메일 번호와 사람의
주소는 모델이 회사 손의 답을 그대로 링크 꼴로 옮기고, 코드는 그 링크만 값으로 읽는다 — 글을 갈라 값을 짐작하지 않는다.

## 조각의 지도

싣는 방향은 한쪽이다 — 아래 줄의 층은 위 줄의 층을 모른다. 조각끼리 고리도, 함수 안에서 늦게 싣는 조각도 없다(함수 안에서 싣는 것은
윈도 전용 모듈 · OS 잠금 모듈뿐이다). 같은 층끼리 싣는 자리는 둘이다 — 마무리(`finish.py:29`)가 일정 손의 미리 보기를 창 곁의 손의
`presses.run_calendar` 로 부르고(다른 프로그램을 띄우는 자리를 늘리지 않으려), 맞춤 파일(`prefs_file.py:19`)이 옛 꼴 읽기(`old_forms`)를 싣는다.

창의 스크립트 `report.js` 는 한 파일이고(CSP 가 지을 때 그 글 하나의 해시만 연다),
기능(줄의 단추 · 보고 시각 · 두 목록 · 일정 넣기 · 자리 밖에서 보기 · 부탁 · 맡길 일)마다 제 함수 범위에 살며 바탕(열쇠 · 저장소 · 때의 꼴 ·
지금 모습)만 함께 쓴다 — 한 기능의 이름이 다른 기능의 이름을 덮지 못한다.

### `unattended/` — 사람 없이 도는 일

정한 시각의 시계와 맡긴 일의 실행은 `scripts/` 와 울타리가 달라 같은 스킬의 다른 폴더에 산다. `scripts/` 는 메일에서 온 글을 품은 창을 다루는 손이라
표준 라이브러리와 제 폴더만 싣고 정해 둔 명령줄 몇만 띄운다(아래 「검사가 남는 까닭」의 「홀로 선다」). `unattended/` 는 claude 를 띄우고 · 사내 중계로
본인 메일을 보내고 · 작업 스케줄러를 걸고 · 로그인 입구를 부른다 — 그 몫을 `scripts/` 에 섞으면 창의 울타리에 구멍이 뚫린다.

싣는 방향은 `unattended/` 가 `scripts/` 를 싣는 한쪽이다 — `scripts/` 는 `unattended/` 를 싣지 않고 입구 명령줄로만 부른다(`presses.run_unattended`). 창의
울타리는 「창의 손이 무엇에 닿나」를 지키는 것이라, 더 넓은 쪽이 좁은 쪽의 코드를 싣는 것은 좁은 쪽이 닿는 데를 늘리지 않는다. 그 덕에 보고 글 이름 ·
디버깅 포트 이름 · 바꿔 끼우는 쓰기 · OS 잠금을 사본 없이 `scripts/` 의 원본(`brief_const` · `store` · `oslock`)에서 쓴다. 형제 스킬 중 코드를 싣는 것은
회사 메일 손 곁의 `mailer`(보내는 손 하나)뿐이고 나머지는 명령으로 부른다. 스캔은 이 폴더 어디에도 코드로 안 실린다 — 시계가 `scan.py run` · `status`
를 명령으로 부를 뿐이다.

맡긴 판의 claude 에 주는 부탁 글의 틀은 `unattended/handed-run.md` 다 — 누름이 곧 승인 · 줄의 값 그대로 · 못 끝내면 바꾸지 않고 멈춘다.

아래는 코드에서 뽑은 지도다 — 두 폴더(`scripts/` · `unattended/`)를 함께 든다. `unattended/` 의 모듈은 「unattended/이름」 으로 서고, 그
폴더의 손이 이름으로 싣는 `scripts/` 의 바탕은 그 이름 그대로 선다. 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을
고치고 다시 짓는다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `unattended/clock.py` · 입구 | 정한 시각의 시계 — 일일 보고를 정한 시각마다 사람 없이 띄우고, 보고 창에서 고르신 것 · 누르신 「일정에 넣기」를 받는 작업과 그 시각표를 걸고 · 보이고 · 내린다. | `cli` · `unattended/clock_setup` · `unattended/clock_tick` · `unattended/loan` · `unattended/scan_door` · `unattended/unattended_const` | — |
| `ticks.py` · 입구 | 보고 창에서 누르신 것을 로그인 Edge 에서 거둔다 — 일일 보고 스킬의 거두는 손. 「끝났음」 · 푸신 「끝났음」은 가장 늦은 보고 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에, 「내일 다시」 · 「이런 건 빼기」 · 「다시 넣기」는 보고 맞춤 파일(곁의 `prefs.py`)에 옮기고, 끝에 이 보고가 보고에서 빼는 것 · 오늘 돌아온 것 · 아직 미룬 것을 댄다. | `brief_const` · `brief_files` · `brief_inline` · `brief_sections` · `cli` · `clock` · `edge` · `prefs` · `prefs_file` · `press_kinds` · `presses` · `report_reads` · `state` · `store` · `window_door` | — |
| `window.py` · 입구 | 보고 글(md)을 보고 창의 틀에 채워 그날의 HTML 로 남기고, 그 글을 곁에 남기고, 브라우저로 띄운다 — 일일 보고 스킬의 내는 손. | `asks` · `brief_const` · `brief_files` · `brief_inline` · `brief_sections` · `brief_text` · `cli` · `clock` · `edge` · `finish` · `hand_wanted` · `prefs_file` · `presses` · `render` · `render_mail` · `state` · `store` · `window_words` | — |
| `unattended/handed.py` · 입구 | 맡긴 일 — 보고 창에서 사람이 골라 맡긴 일들을 작업 폴더에서 claude 한 번으로 차례로 하게 뒤에 띄우고, 도는 동안 일마다의 끝을 프로그램이 읽는 기록으로 낸다. | `clock` · `detach` · `proc_base` · `unattended/brief_schedule` · `unattended/launch_base` · `unattended/loan` · `unattended/scan_door` · `unattended/session_login` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `prefs.py` · 입구 | 보고 맞춤의 대화 명령 — 사용자가 대화에서 「이런 건 빼기」 · 「내일 다시」 하신 것을 보고 맞춤 파일에 보이고 더하고 걷고, 열린 보고 창에 바로 알린다. | `brief_const` · `brief_inline` · `cli` · `clock` · `prefs_file` · `state` | — |
| `unattended/away_sender.py` · 입구 | 자리 밖에서 보기의 보내는 손 — 시계 판이 사람 없이 띄운 보고가 지은 보고 한 장을 메일 한 장으로 지어 표준 입력으로 주면, 사용자가 켤 때 적어 둔 본인 주소 하나를 받는 사람과 보내는 사람으로 삼아 회사 메일 손의 사내 중계(`mailer.py` 의 `send`)로 한 통 보낸다. | `unattended/brief_schedule` · `unattended/unattended_const` · `unattended/unattended_store` | company-mail 의 `mailer` |
| `unattended/clock_tick.py` | 시계 한 판의 겉 — 작업 스케줄러가 주기마다 부르는 `clock.py tick` 의 손. OS 잠금을 쥐고, 옛 파일을 옮겨 받고, 그날 장부를 읽어 이 판의 때를 먼저 적은 뒤 판 한 번(`clock_round.round_lines`)을 하고 장부를 다시 쓴다. | `clock` · `oslock` · `unattended/clock_book` · `unattended/clock_round` · `unattended/scan_door` · `unattended/take_over` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/clock_round.py` | 정한 시각의 시계 한 판 — 자리 밖에서 보기의 메일 → 보고 창에서 고르신 것 → 지금 칸의 띄우기 → 「일정에 넣기」 누름 거두기를 이 차례로 엮고 맨 끝에 사람의 로그인을 돌려준다. | `clock` · `ticks` · `unattended/away_mail` · `unattended/brief_day` · `unattended/brief_kinds` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_state` · `unattended/brief_told` · `unattended/brief_window` · `unattended/brief_words` · `unattended/claude_launch` · `unattended/loan` · `unattended/scan_door` · `unattended/session_login` · `unattended/unattended_const` · `unattended/window_link` · `window_door` | — |
| `unattended/clock_setup.py` | 시계 걸기 · 보고 시각표 · 보기 · 끄기 · 옮겨 받기 — `clock.py register · at · off · away · window-times · status · unregister · adopt` 의 손. 작업 스케줄러의 시계 작업 하나(`clock_task`)와 보고 시각표(`brief_schedule`)를 걸고 · 보이고 · 내린다. | `clock` · `unattended/away_mail` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_status` · `unattended/brief_window` · `unattended/brief_words` · `unattended/claude_launch` · `unattended/clock_book` · `unattended/clock_task` · `unattended/launch_base` · `unattended/scan_door` · `unattended/session_login` · `unattended/take_over` · `unattended/task_base` · `unattended/unattended_const` · `unattended/unattended_store` · `unattended/window_link` | — |
| `unattended/away_mail.py` | 자리 밖에서 보기 — 켠 PC 에서 사람 없이 띄운 보고가 남긴 보고 글 한 장을 칸마다 한 통 본인 메일로 보내고, 켜고 끄기를 건다. | `clock` · `proc_base` · `state` · `unattended/brief_day` · `unattended/brief_kinds` · `unattended/brief_reports` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_state` · `unattended/brief_told` · `unattended/brief_words` · `unattended/clock_book` · `unattended/unattended_const` · `unattended/unattended_store` · `unattended/window_link` | — |
| `unattended/brief_status.py` | status 의 보고 예약 줄 — 걸었나 · 자리 밖에서 보기 · 경고 · 지난날 · 오늘 로그인 · 오늘 돌려준 로그인 · 시각마다 오늘 어떻게 됐나를 차례로 엮는다. | `clock` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_state` · `unattended/brief_told` · `unattended/brief_words` · `unattended/loan` | — |
| `finish.py` | 보고 글을 남기기 전에 코드가 든 값으로 마무리한다 — 창을 여는 손(`window.py`)이 모델이 쓴 글을 받아 창을 짓기 전에 부른다. | `brief_cards` · `brief_const` · `brief_files` · `brief_inline` · `brief_put` · `brief_sections` · `brief_tasks` · `brief_text` · `prefs` · `prefs_file` · `presses` · `store` | — |
| `render.py` | 보고 창을 그린다 — 읽은 보고 글(`brief_text.Report`)과 창이 보이는 지금 모습을 보고 창의 HTML(`build` · 틀 `assets/report.html` · 스크립트 `assets/report.js`)로. 같은 글의 메일 한 장은 곁의 `render_mail.py` 가, 둘이 함께 쓰는 줄 안의 한 걸음(`inline_walk`)은 `render_base.py` 가 든다 — 이 파일은 창의 겉(`WindowSkin`)만 끼운다. | `brief_cards` · `brief_const` · `brief_inline` · `brief_people` · `brief_sections` · `brief_tasks` · `brief_text` · `clock` · `prefs` · `prefs_file` · `render_base` · `task_kinds` | — |
| `report_reads.py` | 보고를 짓는 쪽이 거두는 손(`ticks.py`)의 끝 줄 앞에서 읽을 무리 — 맞춤(보고에서 빼는 것 · 돌아온 것 · 미룬 것), 그리고 가장 늦은 보고 글 뒤에 창에서 누르신 「일정에 넣기」의 끝과 맡기신 일의 끝. 「지난 보고 뒤」는 가장 늦은 보고 글의 이름에서 한 번 읽고, 두 기록은 저마다 제 시계의 꼴로 견준다. | `brief_const` · `brief_files` · `clock` · `presses` · `records` | — |
| `unattended/brief_told.py` | 그날 장부와 아직 말하지 않은 칸 — 그날 장부를 열 때 지난날 건너뛴 칸의 줄을 남기고, 띄우는 보고의 부탁 글에 실을 줄을 엮는 손. | `unattended/brief_day` · `unattended/brief_slots` · `unattended/brief_state` · `unattended/brief_words` | — |
| `presses.py` | 보고 창에서 누르신 것을 누름 종류 표(`KINDS` — 열쇠 · 거둘 때인가 · 할 일 · 돌려 적을 칸)대로 거둬 그 할 일을 부르고 끝을 그 창에 돌려 적는다 — 일일 보고 스킬의 창 곁의 손. 「일정에 넣기」는 사람이 누른 카드의 값과 열쇠로만 일정 손(형제 스킬 company-calendar 의 `add`)을 부른다. | `asks` · `brief_const` · `brief_inline` · `brief_put` · `brief_tasks` · `cli` · `clock` · `detach` · `edge` · `hand_wanted` · `oslock` · `press_kinds` · `proc_base` · `records` · `runs` · `state` · `store` · `task_kinds` · `unattended_link` | — |
| `unattended/brief_day.py` | 그날 칸 장부 — 지금 모습(`state["brief"]`) 안의 그날 칸을 열고 고른다. | `state` · `unattended/brief_kinds` · `unattended/brief_slots` · `unattended/brief_state` | — |
| `unattended/loan.py` | 사람의 로그인을 돌려준다 — 이 PC 의 프로그램이 사람 없이 세운 사내 로그인(그 로그인이 사람의 평소 Edge 의 EP 포털을 죽였다)을 다 쓰면 형제 스킬 ep-login 입구의 돌려주는 문을 사람 없는 꼴로 한 번 부른다(`session_login.give_back` — 평소 Edge 에 로그인을 다시 열고 쓸모가 끝난 EP 탭을 닫는다). 빌린 로그인은 둘이다 — 시계가 보고 시각에 끊긴 세션 위에서 세운 것(그날 장부의 로그인 기록)과, 돌려준 날 보고 창의 단추(「일정에 넣기」 · 「결재 창 열기」 · 「맡기기」)가 세션을 쓰려다 끊겨 있어 잠깐 다시 세운 것(빌림 파일 `LOAN_FILE`). 둘 다 이 조각 하나가 OS 잠금(`LOAN_LOCK_FILE`) 아래에서 빌리고 돌려준다 — 시계 판 · 창 곁의 손 · 맡긴 일의 지킴이가 함께 불러도 한 번이다. | `clock` · `oslock` · `state` · `unattended/brief_reports` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_state` · `unattended/clock_task` · `unattended/scan_door` · `unattended/session_login` · `unattended/task_base` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/window_link.py` | 보고 창 이음 — 같은 스킬의 보고 창 손(`window.py --sheet` · `ticks.py --times-done` · `--away-done` · `--presses`)을 사람 없는 실행에서 프로세스로 부르고, 대화에서 시각표를 바꾼 뒤 열린 창에 알리는(`state.sync`) 유일한 자리. 고르신 것을 읽는 쪽은 창의 문이 함수로 낸다 (`window_door.read_choices`). | `brief_const` · `edge` · `proc_base` · `state` · `unattended/unattended_const` | — |
| `window_door.py` | 시계 판이 쓰는 창의 문 — 열린 보고 창에서 고르신 보고 시각 · 「자리 밖에서 보기」를 읽어 시계 판에 값으로 내고(`read_choices` — 같은 스킬의 `unattended/` 가 함수로 부른다), 시계가 받았나를 그 창의 그 칸에 돌려 적는다(거두는 손 `ticks.py` 의 `--times-done` · `--away-done`). 창 곁의 손과 같은 누름 종류 표의 줄(`press_kinds.TIMES` · `press_kinds.AWAY`)로 재고 적는다. | `brief_const` · `cli` · `edge` · `press_kinds` · `state` | — |
| `state.py` | 창이 보이는 지금 모습 — 사용자 폴더의 보고 시각표 · 그날 장부(사람 없는 실행 `unattended/` 의 파일)와 보고 맞춤 파일에서 짓고(`state_of`), 열린 보고 창에 적는다(`sync` — 저장 열쇠 `brief_const.STATE_KEY`). 사용자 폴더의 파일은 읽기만 한다. | `brief_const` · `brief_inline` · `clock` · `edge` · `prefs` · `prefs_file` · `store` | — |
| `hand_wanted.py` | 창 곁의 거두는 손을 띄울 창인가를 가르는 한 자리 — 창을 여는 손(`window.py`)과 시계 판의 뒷받침(`presses.round_once`)이 같은 자로 잰다. | `brief_inline` · `brief_tasks` · `task_kinds` | — |
| `prefs_file.py` | 보고 맞춤 파일 — 사용자가 보고 창이나 대화에서 「이런 건 빼기」 · 「내일 다시」 하신 것을 사람이 읽는 글로 든다. | `brief_inline` · `brief_sections` · `old_forms` · `prefs` · `store` | — |
| `render_mail.py` | 같은 보고 글에서 휴대폰 너비의 메일 한 장을 짓는다(`mail_sheet`) — 자리 밖에서 보기. 창과 같은 꼴 읽기(`brief_text` · 곁의 `brief_*`)와 같은 줄 안의 걸음 (`render_base.inline_walk`)을 메일의 겉으로 쓴다. | `brief_cards` · `brief_const` · `brief_inline` · `brief_sections` · `brief_tasks` · `brief_text` · `render_base` · `task_kinds` | — |
| `runs.py` | 보고 창의 맡길 일 — 창에서 누른 일들을 뒤의 실행(같은 스킬 `unattended/handed.py`)에 넘기고, 그 실행의 기록을 따라 일마다의 끝을 창에 돌려 적는다. | `brief_const` · `brief_files` · `brief_tasks` · `clock` · `edge` · `presses` · `records` · `store` · `task_kinds` · `unattended_link` | — |
| `unattended/brief_state.py` | 칸의 상태 — 그날 칸 하나가 지금 어느 상태인가를 한 번 셈한다. | `clock` · `unattended/brief_kinds` · `unattended/brief_reports` · `unattended/brief_slots` · `unattended/unattended_const` | — |
| `unattended/brief_window.py` | 보고 창의 고름 걸기 — 보고 창에서 고르신 보고 시각을, 창이 보이던 시각에서 더하고 빼신 것만 걸린 시각표 위에 얹는다. | `clock` · `unattended/brief_kinds` · `unattended/brief_schedule` · `unattended/brief_slots` · `unattended/brief_words` · `unattended/unattended_store` | — |
| `window_words.py` | 창을 여는 손(`window.py`)이 사람에게 하는 말 — 멈춘 까닭 · 경고 · 띄운 곳 · 끝 줄과 「다음:」. 받은 수와 이름만 말로 옮긴다 — 파일 · 프로세스 · 망을 읽지 않는다. | `brief_tasks` · `task_kinds` | — |
| `brief_tasks.py` | 카드에 적힌 맡길 일을 읽는다 — 칸 하나 → `Task`(`task_of` — 종류마다의 셈은 `task_kinds` 의 줄이 든다) · 칸이 든 넣을 일정(`put_in`) · 카드 하나 → 맡길 일과 남은 몫(`take_card`) · 카드로 서나 · 약속의 카드인가 · 시각을 여쭙나(`card_shaped` · `dated_card` · `asks_time`) · 보고 글 → 맡길 일(`tasks_of`) · 일정 넣기를 든 카드(`cards_of`), 맡길 일 하나 → 누를 수 있는 넣을 일정(`pressable_put`) · 창의 할 일 줄의 꼴(`row_shape`). 파일 · 망에 닿지 않는다. | `brief_cards` · `brief_inline` · `brief_put` · `brief_sections` · `brief_text` · `task_kinds` | — |
| `old_forms.py` | 옛 꼴의 말씀을 읽는 한 자리 — 맞춤 파일에 「걸지 않기로 하신 것」 절을 두기 전의 보고 글이 그 말씀을 「이 보고가 본 데」의 한 줄로 들던 꼴. 맞춤 파일을 읽는 손(`prefs_file.read`)이 그 절이 없는 파일일 때만 부르고, 창을 짓는 손의 마무리(`finish.keep_declined`)가 그렇게 읽어 들인 말씀을 맞춤 파일에 한 번 옮긴다. | `brief_files` · `brief_sections` · `store` | — |
| `press_kinds.py` | 누름 종류마다 재는 반 — 창의 저장소 열쇠 · 거둘 때인가(`due`) · 그 창에 돌려 적을 칸(`back`). 창 곁의 손(`presses.KINDS` — 할 일 · 거두는 걸음을 더한다)과 시계 판이 부르는 창의 문(`window_door`)이 이 한 표로 재고 같은 칸을 적는다. | `brief_const` · `clock` · `edge` · `records` | — |
| `unattended/brief_reports.py` | 보고가 섰나 · 끝났나 — 칸의 보고 글을 찾고, 그 칸이 띄운 보고가 끝났나와 남긴 글을 가른다. | `brief_files` · `clock` · `unattended/brief_kinds` · `unattended/brief_slots` · `unattended/launch_base` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/brief_schedule.py` | 보고 시각표 파일 — 사용자 폴더의 `daily-brief-schedule.json` 을 읽고, 시각표를 걸고 내리고, 칸 하나(`away` · `picked`)를 바꿔 쓰는 유일한 자리. | `clock` · `unattended/brief_slots` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/claude_launch.py` | 보고 띄우기 — 사람 없는 보고에 띄울 claude 의 명령 · 열린 명령(권한) · 부탁 글을 짓고, 환경을 손질해 떼어 띄운 뒤 기다리지 않는다. | `clock` · `detach` · `unattended/launch_base` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/clock_book.py` | 그날 장부 파일 — 사용자 폴더의 `daily-brief-day.json` 을 읽고 쓰는 유일한 자리. 그 파일은 그날 장부(날 · 칸들 · 그날의 스스로 로그인)에 시계의 마지막 판 때(`clock_at`)를 얹은 한 장이다. | `clock` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `unattended/take_over.py` | 옮겨 받기 — 메일함 스캔이 보고를 들던 판의 파일(시각표 · 띄운 기록 · 그 출력 · 보내는 중 표지 · 옛 지금 모습 안의 그날 장부)을 이 스킬의 새 이름으로 옮겨 받는 한 자리. `clock.py adopt` 와 시계의 판이 이 하나를 부른다. | `store` · `unattended/unattended_const` · `unattended/unattended_store` | — |
| `asks.py` | 보고 창 머리의 「비서에게 부탁하기」 — 친 말을 채운 Claude Code 대화를 VS Code 의 작업 폴더 창에 연다. | `brief_const` · `brief_inline` · `brief_text` · `store` | — |
| `brief_cards.py` | 줄 · 카드 하나의 생김을 읽는다 — 머리와 때(`card_head`) · 이름(`card_name` · `item_title`) · 앞의 점과 끝의 칸(`split_facts`) · 어느 일인가 (`item_key`). 파일 · 망에 닿지 않는다. | `brief_inline` · `brief_text` | — |
| `brief_sections.py` | 보고 글의 절을 가리고 고친다 — 머리가 그 절을 이르나(`names_section` · `starts_named`) · 절 머리의 종류(`section_kind` · `is_meetings`) · 창에 안 세울 기록 절(`is_empty_done`) · 창에 서는 줄의 차례(`report_items`) · 빠진 끝의 절(`missing_ends`), 글 줄에서 절의 자리(`section_span`) · 줄(`section_rows`) · 기록 절 고치기(`fold`). 파일 · 망에 닿지 않는다. | `brief_inline` · `brief_text` | — |
| `records.py` | 창 곁의 손이 사용자 폴더에 남기는 기록 둘 — 넣은 누름의 기록(열쇠마다 끝)과 맡긴 일의 기록(누름마다 넘긴 판 · 일마다의 끝)을 읽고 쓰는 한 자리, 그리고 맡긴 일의 기록에서 일 하나의 끝을 짚는 길. 없음과 못 읽음은 다른 답이다 — 못 읽은 기록 위에 쓰면 「넣는 중」 · 「넣음」 · 맡긴 판을 잃어 같은 일정을 또 넣고 같은 일을 다시 넘긴다. | `clock` · `presses` · `store` | — |
| `unattended/brief_words.py` | 보고 시각표의 말 — 칸의 상태(`brief_state`)와 시각표를 사람에게 할 말로 옮긴다: 거는 말 · 거절의 말 · status 의 한 시각 · 건너뛴 칸의 줄(부탁 글 · 지난날) · 칸의 메일 기록 · 보고 창에 돌려 적는 말. 셈은 다른 조각이 하고 여기는 말만 짓는다. | `clock` · `unattended/brief_kinds` · `unattended/brief_slots` · `unattended/unattended_const` | — |
| `unattended/unattended_store.py` | 사람 없는 실행의 JSON 파일 한 장 — 일일 보고 바탕(`store`)의 읽기 · 바꿔 끼우기 위에 이 폴더가 기대는 꼴(못 읽은 말 · 글이 깨졌나)을 얹는 한 자리. 바꿔 끼우는 몸은 바탕에 하나다 — 여기는 그 몸을 다시 짓지 않는다. | `clock` · `store` | — |
| `brief_text.py` | 보고 글을 제목 · 절 · 덩이로 가른다(`parse` → `Report` · `Section` · `Block` · `Item`) — 줄의 꼴(머리 · 번호 · 「-」 · 들여 쓴 낱낱 · 인용 · 「@」 시간줄 · 가름줄)만 읽고, 줄 안의 꼴 · 카드 · 절의 뜻은 곁의 읽기(`brief_inline` · `brief_cards` · `brief_sections` · `brief_tasks`)가 든다. | `clock` | — |
| `edge.py` | 로그인 Edge 의 열린 보고 창과 주고받는다 — 일일 보고 손들이 Edge 에 닿는 한 자리. 디버깅 포트(`port`)에 새 탭을 열고(`open_tab`), CDP 웹소켓 하나(`Cdp`)로 열린 보고 창(file: 탭 — `page` · `brief_tabs`)에 붙어 그 창의 저장소(localStorage)를 읽고 쓰고(`Tab`), 읽은 칸을 값으로 푼다(`cells` · `stored` · `pressed_at`). 부르는 곳은 늘 이 PC 의 디버깅 포트(`brief_const.EDGE_HOST`)다 — 메일함에 닿지 않는다. | `brief_const` · `brief_files` | — |
| `store.py` | 일일 보고 손들이 사용자 폴더의 파일(기록 · 맞춤 파일 · 스캔의 설정 · 누른 창의 보고 글)을 읽고 바꿔 끼우는 한 자리 — 없음 · 읽음 · 못 읽음을 가른다. | `brief_files` | — |
| `task_kinds.py` | 맡길 일의 종류마다 한 줄 — 적는 칸 · 값의 차례 · 꼴 · 넘길 값 · 사람 칸 · 사람이 읽는 줄 · 무엇이 되나 · 시작 시각 · 창의 말 · 결과 이름표 · 넘기는 길(`ROWS`). 맡길 일 읽기(`brief_tasks`)가 칸마다 그 줄을 골라 값을 한 번 이름 붙여 읽고(`Kind.read` → `Cells`) 셈해 두며, 창 그림 · 메일 한 장 · 맡길 일 넘기기는 셈한 값만 읽는다 — 파이썬에서 종류로 갈래를 치는 자리는 이 표 밖에 없다. | `brief_inline` · `brief_people` · `brief_put` | — |
| `unattended/brief_slots.py` | 보고 시각표의 칸 셈 — 시각표에서 그날의 칸(시각마다 덮는 첫때 · 시작 · 끝)과 틈을 셈한다. | `clock` · `unattended/unattended_const` | — |
| `unattended/clock_task.py` | 시계의 작업 스케줄러 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `clock.py tick` 을 창 없이(pythonw) 부르게 정의를 짓는다. | `unattended/task_base` · `unattended/unattended_const` | — |
| `unattended/launch_base.py` | 뒤에 사는 claude 를 띄우는 바탕 — 띄울 claude 를 찾고 · 그 환경을 손질하고 · 그 프로세스가 아직 도나 본다. | `unattended/unattended_const` | — |
| `unattended/scan_door.py` | 스캔 이음 — 형제 스킬 mailbox-scan 의 두 문(`scan.py status --json` · `scan.py run --now --wait`)을 부르고 그 답을 읽는 이 폴더의 유일한 자리. 사용자 폴더와 회사 메일 손의 자리도 여기서 정한다 — 사용자 폴더는 스캔이 내준 답에서, 손은 형제 폴더에서. 스캔의 코드는 싣지 않는다(명령으로만 부른다). 문의 칸과 뜻은 그 스킬의 설계 「status --json · run --wait」이 든다. | `clock` · `proc_base` · `unattended/brief_kinds` · `unattended/unattended_const` | — |
| `unattended/session_login.py` | 사내 세션 — 회사 메일 손의 `session` 한 번으로 사내 세션이 살았나를 보고, 보고 시각을 건 PC 에서는 그 시각에 형제 스킬 ep-login 의 입구를 사람 없는 꼴로 부르고, 그 로그인을 다 쓰면 같은 입구의 돌려주는 문으로 사람에게 돌려준다. | `clock` · `proc_base` · `unattended/unattended_const` | — |
| `brief_files.py` | 보고 창(.html) · 보고 글(.md)의 이름을 읽는다 — 지은 때(`made_of`) · 보고 창의 이름인가(`is_window`) · 폴더에 남은 보고 글을 그 차례로(`kept_briefs`). 보고 창 · 글 이름의 꼴을 아는 자리는 이 파일이다 — 이름의 원본은 `brief_const.FILE_NAME` 이다. | `brief_const` | — |
| `brief_people.py` | 사람을 대는 칸의 값을 사람들로 읽는다(`people_in` → `Person`). 파일 · 망에 닿지 않는다. | `brief_inline` | — |
| `brief_put.py` | 일정에 넣을 값 한 칸을 읽는다 — 칸의 값 → `Put`(`put_of`) · 두 시각을 사람이 읽는 때로(`span_words`) · 「시각: 메일에 없음」 칸 떼기(`no_time_of`). 파일 · 망에 닿지 않는다. | `brief_const` · `brief_inline` | — |
| `clock.py` | 일일 보고 손들이 때를 짓는 한 자리 — 서울 벽시계 · 이 PC 의 시각 · 이 PC 의 벽시계 · 기록에 남기는 때의 꼴 · 사람이 읽는 때의 꼴. | `brief_const` | — |
| `detach.py` | 떼어 띄우는 인자 — 띄운 것이 부른 손보다 오래 살게 하는 `Popen` 인자의 한 자리. 창을 안 띄우는 몫은 곁의 `proc_base.quiet` 가 들고, 여기는 다른 프로세스 묶음 · 작업 묶음(job) 밖이라는 몫만 더한다. | `proc_base` | — |
| `render_base.py` | 창과 메일 한 장이 함께 쓰는 그림 바탕 — 줄 안의 꼴을 읽는 한 걸음(`inline_walk` — 겉만 바꿔 끼운다), 지은 때의 꼴, 시각 없는 모임의 말. 파일을 읽지 않고 망에 닿지 않는다. | `brief_inline` | — |
| `unattended/unattended_const.py` | 일일 보고의 사람 없는 실행(정한 시각의 시계 · 맡긴 일)이 쓰는 이름 붙은 값 — 사용자 폴더의 파일 이름 · 시한 · 형제 스킬의 자리 · 띄운 claude 의 울타리. `unattended/` 의 손이 다 여기서 읽는다. | `brief_const` · `unattended/hand_facts` | — |
| `unattended_link.py` | 사람 없는 실행 이음 — 같은 스킬의 `unattended/` 입구 명령(`handed.py start · show · list` · `clock.py away · window-times … --chosen-at`)의 인자를 짓고 그 끝 줄 · JSON 을 읽는 창 곁의 유일한 자리. 프로그램은 띄우지 않는다 — 부르는 쪽이 준 `run`(`presses.run_unattended` — `run(인자, 시한) -> (종료 값, 표준 출력)` · 인자의 첫 칸이 입구의 이름) 하나로 부른다. | `brief_const` | — |
| `brief_const.py` | 일일 보고의 창 · 창 곁의 손 · 형제 스킬과의 이음이 함께 쓰는 이름 붙은 값 — 저장 열쇠 · 시한 · 파일 이름 꼴 · Edge 이름. | — | — |
| `brief_inline.py` | 보고 글 한 줄 안의 꼴을 읽는다 — 고정 글자 · 메일 · 사람 · 방 · 결재 문서 · 절 링크 · 표지 · 굵게(`INLINE`). 맨글자(`plain`) · 첫 메일 번호(`first_unid`) · 번호를 남긴 맨글자(`with_numbers`) · 글자로 쓴 주소의 수(`url_count`). 파일 · 망에 닿지 않는다. | — | — |
| `cli.py` | 보고 창 손의 입구 명령(`window.py` · `ticks.py` · `prefs.py`)이 함께 쓰는 바탕 — 인자 규칙(사람 없는 실행이 연 명령의 꼴 `--dir "<사용자 폴더>"`을 지킨다) · `--help` 의 「프로그램이 부르는 문」 절 · 멈춘 까닭 · 사람에게 할 말 내기. | — | — |
| `oslock.py` | OS 잠금 한 자리 — 파일 하나의 첫 바이트를 잠근다. | — | — |
| `proc_base.py` | 프로세스 바탕 — 곁의 파이썬 손(회사 메일 손 · 형제 스킬의 입구)을 창 없이 · UTF-8 로 띄우는 한 자리. | — | — |
| `unattended/brief_kinds.py` | 칸의 상태의 꼴 — 그날 칸 하나의 상태 이름과 그 셈을 담는 그릇. 셈하는 조각(`brief_state`)이 채우고 말을 짓는 조각(`brief_words`)이 읽는다. | — | — |
| `unattended/hand_facts.py` | 메일함 스캔이 기대는 형제 스킬의 사실 — 회사 메일 손의 자리 · 종료 값 · 시한, 로그인이 사는 스킬, 사내 세션의 답 낱말, 세션이 끊겼을 때 사람에게 이를 다음 걸음. | — | — |
| `unattended/task_base.py` | 작업 스케줄러 바탕 — 비서의 작업 하나를 schtasks · PowerShell 로 걸고 · 묻고 · 지우고 · 정의를 받나 묻고, 그 답을 푼다. | — | — |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 입구 — 맞춤 파일을 열어 받은 하위 명령대로 보이거나 고쳐 쓰고, 열린 창에 알린 뒤 끝 줄을 낸다.
  - `parser` — 인자 — 동사 다섯.
  - `opened` — 쓰기 전에 맞춤 파일을 읽는다 — 폴더가 없거나 못 읽으면 `cli.Stop`(빈 것으로 읽고 쓰면 감추고 미룬 일이 사라진다).
    - `cli.Stop` — 입구가 그 한 줄(`line`)을 사람에게 하고 그 종료 값(`code` — 기본 1)으로 멈춘다 — 손가락이 멈춘 까닭을 들고 올리고, 손은 한 자리에서 받는다.
    - `prefs_file.read` — 맞춤 파일 — 없으면 빈 것. 있는데 못 읽으면 `strict`(읽은 뒤 쓰는 자리)는 `Unreadable`, 보이기만 하는 자리는 빈 것에 못 읽었다는 표 (`unread`)를 단다 — 보이는 쪽이 「없습니다」 대신 못 읽었다고 말한다.
      - `file_text` — 맞춤 파일의 글 — 없으면 빈 글. 있는데 못 읽으면 `strict` 는 `Unreadable`, 아니면 None.
        - `store.read_bytes` — 파일의 바이트 — 없으면 None, 있는데 못 읽으면 `Unreadable`.
          - `Unreadable` — 파일이 있는데 못 읽었다 — 다시 해 봐도 진 OSError · 글이 꼴이 아니다.
        - `path_of` — 사용자 폴더의 보고 맞춤 파일 자리.
      - `Prefs` — 보고 맞춤 파일 한 장 — 보고에서 빼는 것 · 내일 다시 볼 것 · 다시 올린 것 · 걸지 않기로 하신 것과 읽은 꼴.
      - `with_legacy` — 그 절(「걸지 않기로 하신 것」)을 쓰기 전의 파일이고 가장 늦은 보고 글이 옛 꼴로 그 말씀을 들었으면 한 줄로 읽어 들이고 아직 안 적혔다는 표(`legacy`)를 단다 — 창을 짓는 손의 마무리가 맞춤 파일에 옮긴다.
        - `old_forms.declined_old` — 가장 늦은 보고 글이 걸지 않기로 하신 말씀을 「이 보고가 본 데」의 줄로 들었나 — 맞춤 파일에 그 절을 두기 전의 꼴. 못 읽으면 False.
          - `brief_files.kept_briefs` — 폴더에 남은 보고 글 — 이름이 `FILE_NAME` 꼴(.md)인 것만, 이름 차례(곧 지은 때의 차례)로. 거르는 꼴은 이 PC 의 파일 이름 규칙을 따른다 (Windows 는 큰 · 작은 글자를 안 가린다).
            - `made_of` — 보고 창(.html) · 보고 글(.md)의 이름에서 지은 때 — 이 PC 의 시각(`FILE_NAME` 이 그렇게 짓는다). 꼴이 아니면 None.
          - ↑ `store.read_bytes`
          - ↑ `store.Unreadable`
          - `brief_sections.starts_named` — 머리의 글(꼴 표시를 걷었든 안 걷었든 받은 그대로)이 절 이름 `names` 가운데 하나로 시작하나 — 앞뒤 빈칸은 안 본다.
      - `prefs_of` — 맞춤 파일의 글 → 네 절의 줄. 사람이 손으로 고친 파일도 「- 」 줄만 읽는다.
        - ↑ `Prefs`
        - `lines_of` — 절 `name`(「## 」 머리) 아래 「- 」 줄 — 「없음」은 뺀다.
    - ↑ `prefs_file.path_of`
  - `cli.say` — 사람에게 할 말을 줄마다 표준 출력에 낸다.
  - `show_lines` — `show` — 두 절을 번호와 함께, 다시 올린 것 · 걸지 않기로 하신 것은 있을 때만, 그리고 끝 줄. 그 절이 없는 옛 파일이면 걸지 않기로 하신 것은 읽는 손이 지난 보고 글의 옛 꼴 한 줄에서 읽어 들인 것이다.
  - ↑ `prefs_file.path_of`
  - `changed` — 바꾸는 동사 하나를 부른다 — 한 일의 말.
    - `add_quiet` — `quiet` — 사용자의 말을 「보고에서 빼는 것」에 더한다.
      - `prefs_file.clean` — 줄에 들일 글 — 줄바꿈 · 꼴 표시 · 메일 번호 꼴을 걷고 줄인다.
      - ↑ `cli.Stop`
      - `prefs_file.put_quiet` — 「보고에서 빼는 것」에 한 줄 — 같은 열쇠의 줄은 바꾼다.
        - `key` — 줄의 열쇠 — 메일 번호(`unid_of`)가 있으면 그 번호, 없으면 글에서 낸 짧은 지문(「w」 + 10자리). 보고 창의 「다시 넣기」가 이 열쇠로 그 줄을 짚는다.
          - `unid_of` — 줄에 단 첫 메일 링크(`MAIL_LINK`)의 번호(대문자) — 없으면 None.
        - ↑ `unid_of`
      - `clock.day_words` — 사람이 읽는 날 — 「M/D」.
    - `add_later` — `later` — 그 일을 「내일 다시 볼 것」에 더한다(돌아오는 날은 내일). 메일 번호가 32자리가 아니면 `cli.Stop`.
      - ↑ `cli.Stop`
      - `prefs_file.put_later` — 「내일 다시 볼 것」에 한 줄 — 같은 메일의 줄(다시 올린 것도)은 바꾸고, 그 메일의 「보고에서 빼는 것」 줄은 걷는다.
        - ↑ `unid_of`
      - ↑ `prefs_file.clean`
      - ↑ `clock.day_words`
    - `note_declined` — `decline` — 처음 보고 때 여쭌 메일함 스캔 · 아침 보고를 마다하신 것을 적는다.
    - `forget_row` — `forget` — 「보고에서 빼는 것」(`later` 면 「내일 다시 볼 것」)의 그 번호 줄을 걷는다.
      - ↑ `cli.Stop`
  - `clock.wall_now` — 지금 — 이 PC 의 벽시계(시간대 없이). 보고 글 · 창 파일의 이름이 이 시각으로 선다.
  - `saved` — 맞춤 파일을 쓴다 — 못 쓰면 `cli.Stop`.
    - `prefs_file.write` — 맞춤 파일을 곁의 임시 파일에 다 쓴 뒤 바꿔 끼운다 — 다시 올린 것은 줄이 있을 때만 선다.
      - `store.replace` — 곁의 제 임시 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 파일이 남지 않는다.
      - ↑ `path_of`
    - ↑ `cli.Stop`
    - ↑ `prefs_file.path_of`
  - ↑ `cli.Stop`
  - `state.sync` — 열린 보고 창에 지금 모습을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다). 내는 것 — 한 줄(못 했으면 "").
    - `edge.tell_open` — 열린 보고 창에 칸들(`rows()` 의 답)을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다 · `rows` 도 안 부른다). 적었나.
      - `window` — 열린 보고 창 하나에 붙은 동안 — 그 탭(`page` — 열린 것이 없으면 `fallback` 을 뒤 탭으로 연다)을 낸다.
        - `connected` — 로그인 Edge 의 디버깅 포트에 붙은 동안 — 그 이음(`Cdp`)을 낸다.
          - `Cdp` — 부르는 곳은 늘 `brief_const.EDGE_HOST` 다 — 디버깅 포트의 답에 든 주소에서는 길(path)만 쓴다.
            - `port` — 로그인 Edge 의 디버깅 포트 — `EDGE_DEBUG_PORT` 의 첫 것, 꼴이 아니면 기본. 창을 여는 손과 거두는 손이 같은 포트를 본다.
            - `EdgeGone` — 로그인 Edge 에 못 닿았거나 그 답이 꼴이 아니다 — 표시는 그 Edge 에 남는다.
            - `Cdp._handshake` — Origin 을 안 싣는다 — Chromium 은 Origin 이 든 손잡기만 --remote-allow-origins 로 거른다.
              - ↑ `port`
              - `Cdp._fill` — 웹소켓에서 받은 바이트를 남은 몫에 덧붙인다 — 끊겼으면 EdgeGone.
                - ↑ `EdgeGone`
              - ↑ `EdgeGone`
            - ↑ `Cdp._fill`
            - `Cdp._take` — 받은 바이트의 앞 `n` 바이트를 떼어 낸다 — 모자라면 더 받는다.
              - ↑ `Cdp._fill`
            - `Cdp._send` — 보내는 틀은 늘 가린다(mask) — RFC 6455 가 손님 쪽에 시키는 것이다.
            - `Cdp._message` — 웹소켓 글 하나를 받는다 — 조각을 잇고, 핑에는 퐁으로 답하고, 닫힘이면 EdgeGone.
              - ↑ `Cdp._take`
              - ↑ `EdgeGone`
              - ↑ `Cdp._send`
            - `Cdp.call` — 명령 하나를 보내고 같은 번호의 답을 기다린다 — 사이에 오는 사건은 버린다.
              - ↑ `Cdp._send`
              - ↑ `Cdp._message`
              - ↑ `EdgeGone`
            - `Cdp.evaluate` — 탭(`session`)에서 식 하나를 돌려 그 값을 낸다 — 식이 넘어지면 EdgeGone.
              - ↑ `Cdp.call`
              - ↑ `EdgeGone`
            - `Cdp.close` — 닫힘 틀을 보내고 소켓을 닫는다 — 이미 끊겼으면 그대로 둔다.
              - ↑ `Cdp._send`
          - ↑ `port`
          - ↑ `EdgeGone`
          - `NoEdge` — 처음부터 로그인 Edge 에 못 닿았다(주고받다 멈춘 것과 다른 끝) — 표시는 그 Edge 에 남는다.
        - `page` — 표시를 읽고 쓸 file: 탭 하나 — 열린 것이 있으면 그것, 없으면 보고 창(`fallback`)을 뒤 탭으로 열고(닫을 때 닫는다) file: 문서가 서기를 기다린다.
          - `NoWindow` — 열린 보고 창(file: 탭)이 없다 — 새로 열지 않는 부름(창의 문 `window_door` 의 고름 읽기 · 돌려 적기)이 받는다.
          - `Tab` — 열린 보고 창 하나 — 붙어 읽고 쓴다.
            - ↑ `Cdp`
            - `Tab.filed` — file: 문서가 섰나 — 새 탭은 about:blank 에서 옮겨 가는 동안 식이 문맥을 잃고 넘어질 수 있어, 그것도 「아직」으로 본다.
              - ↑ `EdgeGone`
            - `Tab.read` — 저장소의 (열쇠, 값) 가운데 열쇠가 `prefixes` 의 하나로 시작하는 것. 답이 JSON 글이 아니면 EdgeGone.
              - `read_expr` — 열쇠가 `prefixes` 의 하나로 시작하는 칸을 (열쇠, 값)의 JSON 으로 내는 식.
              - ↑ `EdgeGone`
            - `Tab.write` — 칸들(열쇠, 값)을 창의 저장소에 적는다 — `quiet` 면 창이 다시 그리게 하는 저장소 사건을 안 일으킨다.
            - `Tab.swap` — 그 열쇠의 값이 아직 `old` 그대로면 `new` 로 바꾼다 — 바꿨으면 True. 창의 글 하나 안에서 읽고 쓰므로 그 사이에 창이 쓸 틈이 없다.
            - `Tab.close` — 이 손이 뒤 탭으로 연 탭이면 그 탭을 닫는다 — 사람이 연 창은 두고, 못 닫아도 그대로 둔다.
              - ↑ `EdgeGone`
          - ↑ `EdgeGone`
      - ↑ `EdgeGone`
      - ↑ `NoWindow`
    - `row` — 열린 창에 적을 지금 모습의 칸 하나 — (저장 열쇠, 지금 모습의 JSON).
      - `state_of` — 창이 보이는 지금 모습 — 사용자 폴더의 두 파일(보고 시각표 · 보고 맞춤 파일)에서 끌어낸다.
        - `read_json` — 사용자 폴더의 JSON 한 장 — 없으면 빈 것, 있는데 못 읽으면 빈 것에 더해 `UNREAD` 에 그 이름을 남긴다(보이기만 하는 자리 — 쓰지 않는다).
          - `store.read_json` — JSON 사전 하나 — 없으면 None, 못 읽거나 꼴이 아니면 `Unreadable`.
            - ↑ `read_bytes`
            - ↑ `Unreadable`
          - ↑ `store.Unreadable`
        - `schedule_from` — 읽은 보고 시각표 → (걸린 보고 시각표, 건 때) — 시각이 없으면 (None, …). 시각 하나를 쓰던 꼴(`at`)도 읽는다.
        - ↑ `prefs_file.read`
        - ↑ `prefs_file.Prefs`
        - `minutes` — 시각표에 적힌 규칙의 수(분) — 하루 안의 양의 정수가 아니면 None.
        - `signed_from` — 시각표 파일에 시계가 남긴 스스로 로그인한 보고의 범위 — {at 로그인한 때, until 그 보고가 글을 남길 수 있는 끝}(원본은 사람 없는 실행 `unattended/` 의 `brief_schedule.note_signed`). 둘 다 시간대를 단 ISO 꼴일 때만 낸다 — 없거나 꼴이 아니면 None(그 한 줄이 안 설 뿐이다).
        - `pref_row` — 맞춤 파일의 줄 하나 → 창이 세울 칸 — 열쇠 · 메일 번호 · 링크를 걷은 맨글자 · 돌아오는 날.
          - ↑ `prefs_file.key`
          - ↑ `prefs_file.unid_of`
          - `brief_inline.plain` — 꼴 표시를 걷은 맨글자 — 창의 이름(<title>)에 쓴다.
          - `prefs_file.due_of` — 「내일 다시」 줄이 돌아오는 날 — 꼴이 아니면 None(그런 줄은 바로 돌아온 것으로 본다).
        - `clock.stamp` — 기록에 남기는 때 — 초까지의 ISO 꼴.
        - `clock.local_now` — 지금 — 이 PC 의 시각(시간대를 단다).
  - `done_words` — 끝 줄 — 한 일 · 맞춤 파일의 자리 · 열린 창에 알렸으면 그 말.
- `main` — 명령 입구 — 받은 문(누름 넣기 · 창 곁 · 돌려 적기)을 그 손에 나누고, 문이 없으면 거둔다(`gather`).
  - `parser` — 인자 — 모델의 길(거두기)과 프로그램이 부르는 문(시계 판의 셋 · 창 곁의 손)을 `--help` 의 다른 절에 둔다.
    - `cli.Once` — 두 번째로 오면 인자 오류(종료 2)로 멈춘다 — 줄인 이름(`--di`)이나 `--dir=…` 꼴로 와도 같은 칸이라 함께 걸린다.
  - `presses.watch` — 창 곁의 손 — 열린 보고 창이 있는 동안 `STEP_S` 마다 누름을 거두고 `C.HAND_BEAT_S` 마다 숨 표를 적는다.
    - `oslock.OsLock` — 파일 하나의 첫 바이트를 잠근다 — 못 쥐면 `take` 가 False. 시각으로 푸는 잠금과 달리 죽은 손을 「도는 중」으로 잘못 읽지 않는다.
      - `OsLock.take` — 잠금을 쥐어 본다 — 쥐었으면 True, 다른 손이 쥐었거나 파일을 못 열면 False.
      - `OsLock.release` — 쥔 잠금을 풀고 파일을 닫는다 — 안 쥐었으면 아무것도 안 한다.
    - `log` — 창 곁의 손의 기록 파일에 때와 한 줄을 남긴다(`fresh` 면 새로 쓴다) — 못 쓰면 그냥 지나간다.
      - ↑ `clock.stamp`
      - `clock.seoul_now` — 지금 — 서울 벽시계.
    - `Hand` — 창 곁의 손의 한 판 — 붙은 창 · 숨 표를 적은 때 · 맡긴 일(`runs.Runs`)을 든다.
      - `runs.Runs` — 창 곁의 손이 든 맡긴 일 — 기록을 쥐고, 걸음마다 새 누름을 맡고 도는 판을 따르고 창에 적는다.
        - `Runs.load` — 기록 — 못 읽으면 None(그 위에 안 쓴다 · 새 누름을 안 넘긴다).
          - `records.read_runs` — 맡긴 일의 기록 — {누름의 열쇠: 누름}. 파일이 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `Unreadable`.
            - ↑ `store.read_json`
        - `Runs.save` — 맡긴 일의 기록을 파일에 쓴다 — 썼으면 True, 못 쓰면 False.
          - `records.write_runs` — 새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다.
            - ↑ `clock.stamp`
            - ↑ `clock.local_now`
            - `live` — 맡긴 누름 하나가 아직 살아 있나 — 넘기는 중 · 도는 중. 판의 상태가 셋 밖인 누름(손으로 고친 기록)은 살아 있지 않다 — 따르는 길이 없어 영영 안 맺히고, 살아 있다고 읽으면 창 곁의 손이 안 끝난다.
            - ↑ `store.replace`
        - `Runs.busy` — 넘기는 중 · 도는 판이 있나 — 있으면 창 곁의 손이 열린 창이 없어도 남아 끝을 받는다.
          - ↑ `Runs.load`
          - ↑ `records.live`
        - `Runs.sessions` — 이 손이 넘긴 판의 세션 — 창의 「대화로 이어 가기」가 들고 온 세션을 여기에 대 본다(창의 저장소는 file: 창끼리 하나라 믿지 않는다).
          - ↑ `Runs.load`
        - `Runs.adopt` — 손이 없을 때 창이 「못 맡김」으로 맺은 누름 가운데 그 일이 다 이 손이 넘긴 판에 들었거나 다시 넘기면 안 될 끝으로 맺은 것을 그 판을 따르는 누름으로 받는다 — 창에서 그 일이 「못 맡김」으로 서 있는데 실제로는 돌거나 됐으면 사람이 또 맡긴다.
          - `press_page` — 누름의 열쇠(`<창 이름>~<ms>`)에서 창 이름.
          - `live_or_settled` — 그 일이 이미 넘겨져 돌거나 다시 넘기면 안 될 끝으로 맺었으면 그 누름의 열쇠 — 다시 넘겨도 되면 None.
            - `last_of` — 그 보고의 그 일을 든 가장 늦은 누름(`but` 은 빼고) — (열쇠, 누름).
            - `records.task_outcome` — 맡긴 일의 기록에서 그 누름의 그 일의 끝 — 따르는 누름이면 따르는 판의 것.
            - ↑ `records.live`
          - ↑ `clock.stamp`
          - ↑ `clock.local_now`
        - `Runs.orphans` — 창에 맡았다고 적혔는데 기록에 없는 누름의 칸 — 손이 「넘기는 중」을 남기기 전에 멈췄다(넘기기는 그 기록을 남긴 뒤에만 한다). 그래서 넘긴 것이 없다 — 「못 맡김」과 그 까닭으로 맺는다.
          - ↑ `clock.stamp`
          - ↑ `clock.local_now`
          - `refuse_rows` — 맡지 않은 누름의 칸 — 누름은 맺고 일마다 「못 함」과 그 까닭. 아무것도 안 넘겼다.
            - ↑ `press_page`
            - ↑ `clock.stamp`
            - ↑ `clock.local_now`
        - `Runs.take` — 새 누름을 맡기만 한다 — 맡을 누름마다 `take_one`. 다른 프로그램을 안 불러 곧 끝나므로, 넘기거나 따르느라 걸음이 길어진 동안에도 기다리는 손이 불러 누름을 `brief_const.RUN_TAKE_S` 안에 맡는다(넘기기는 `step` 이). 기록에 남길 구절들을 낸다.
          - ↑ `Runs.load`
          - `Runs.take_one` — 누름 하나를 맡는다 — 창에 맡았다고 적고(그 사이 창이 맺었으면 안 맡는다) 기록에 「넘기는 중」을 남긴다.
            - ↑ `clock.stamp`
            - ↑ `clock.local_now`
            - ↑ `refuse_rows`
            - `hand_over` — 누름 하나를 가른다(창에 맡았다고 적은 뒤다) — {entry: 기록에 남길 누름, go: 실행에 넘길 일}. 이미 넘겨진 일은 그 판을 따르고(`held`), 못 할 일은 그 까닭으로 맺는다.
              - ↑ `press_page`
              - ↑ `clock.stamp`
              - ↑ `clock.local_now`
              - `store.page_brief` — 누른 창(`page` — 그 창의 파일 이름)의 보고 글 — (같은 이름의 .md 의 자리, 글). 창을 지은 글이다 — 카드 · 맡길 일은 창이 선 뒤 안 바뀌고, 끝의 기록 절만 거두는 손(곁의 `ticks.py`)이 고친다.
                - `brief_files.is_window` — 파일 이름이 보고 창의 이름(`FILE_NAME` 꼴 · .html)인가 — 누른 창 · 열린 탭 · 창의 보고 글을 찾는 자리가 이 한 자로 가른다.
                  - ↑ `made_of`
                - ↑ `read_bytes`
                - ↑ `Unreadable`
              - `brief_tasks.tasks_of` — 보고 글의 맡길 일 — {일의 번호: Task}. 창 곁의 손이 누름의 번호를 이 글의 카드에 대어 그 값과 근거로 한다 — 창이 사람에게 보인 글과 같은 글이다.
                - `Task` — 카드에 적힌 맡길 일 하나 — 칸의 값과 그 종류의 줄(`row` — `task_kinds` 의 한 줄), 그 줄이 셈한 사람이 읽는 줄 · 무엇이 되나 · 시작 · 넘길 값(`task_of` 가 한 번 셈한다). 창이 사람에게 보이는 줄과 창 곁의 손이 넘겨받는 일이 다 이것에서 나온다(`tasks_of`). 꼴이 틀린 칸은 종류가 `task_kinds.BAD` 다 — 그 줄은 적힌 글(`written`) 그대로 서고 맡길 수 없다.
                  - `task_kinds.Kind` — 맡길 일 종류 하나 — 카드에 적는 이름 · 넘기는 길 · 적는 칸 · 값의 차례 · 셈(꼴 · 넘길 값 · 줄 · 무엇이 되나의 칸 · 시작) · 사람 칸 · 창의 말 · 결과 이름표. 셈은 이름 붙은 값(`Cells`)과 넣을 일정 · 사람이 읽는 칸의 말(`Shown`) · 사람 칸의 사람들을 받는다 — 맡길 일 읽기(`brief_tasks.task_of`)가 칸마다 한 번 부르고, 부르는 쪽은 셈한 값만 읽는다.
                    - `Cells` — 맡길 일 한 칸의 값을 이름으로 — 그 종류의 차례(`Kind.cells`)대로 읽은 것(`read_cells`). 머리말(「참석 」 · 「안내 」 · 「메일 」)은 뗐고, 그 종류에 없는 칸은 빈 글이다.
                    - `brief_put.Put` — 카드 하나가 넣을 일정 — 창이 사람에게 보이는 글과 거두는 손이 일정 손에 주는 값이 다 이것에서 나온다.
                      - `Put.words` — 사람이 읽는 「무엇을 넣나」 — 날 · 요일 · 시각 · 제목 · 곳. 공개 범위는 따로(`VIS_WORDS`).
                        - `span_words` — 「11월 26일(목) 14:00–16:00」 — 서울 벽시계 두 시각(`PUT_STAMP` 꼴)을 사람이 읽는 때로. 날을 넘기면 끝의 날도 댄다.
                          - `put_moment` — 일정 손의 시각(`PUT_STAMP` 꼴 — 거른 글만 준다) → 서울 시간대가 붙은 때. 꼴이 아니면 ValueError.
                    - `Shown` — 사람이 읽는 칸의 말 — 꼴이 맞은 값(`Cells`)과 사람 칸의 사람들에서 한 번 짓는다(`shown_of`). 줄을 짓는 셈(`Kind.line`)은 이것을 옮기기만 한다.
                    - `no_fill` — 무엇이 되나에 채울 칸이 없다.
                    - `Kind.read` — 칸의 값 → 이 종류의 차례로 이름 붙인 값(`read_cells`). 값을 넣을 일정이 드는 종류는 빈 `Cells`.
                      - ↑ `Cells`
                      - `read_cells` — 칸의 값(「 | 」로 가른 그대로) → 이름 붙은 값. `order` 의 칸이 그 차례로 다 있고 `extra` 의 칸은 있으면 그 뒤에 선다 — 칸마다 (이름, 머리말). 칸 수가 모자라거나 넘치거나 · 빈 값이 있거나 · 머리말이 빠졌으면 None(고쳐 읽지 않는다).
                        - `after` — 칸의 머리말(「참석 」 · 「안내 」 · 「메일 」, 없으면 빈 글)을 뗀 값.
                        - ↑ `Cells`
                    - `Kind.persons` — 사람 칸(`people`)의 사람들 — 칸이 없거나 사람 링크의 꼴이 아니면 빈 것.
                      - `brief_people.people_in` — 사람을 대는 칸의 값 → 사람들. 꼴이 아니면 None — 값은 사람 링크(뒤에 괄호 덧말 하나까지)를 「 · 」로 이은 것이고 끝의 표지({…})는 걷고 잰다.
                        - ↑ `brief_inline.plain`
                        - `Person` — 사람 링크 하나 — 사람이 읽는 이름(직함까지) · 그분을 가르는 주소 · 링크 뒤 괄호의 덧말.
                          - `Person.said` — 사람이 읽는 꼴 — 「이름 직함(덧말)」.
                    - `Kind.said` — 누르시면 무엇이 되나 — `cons` 에 그 값과 사람들로 채운 칸을 넣은 말.
                  - ↑ `brief_put.Put`
                  - `Task.kind` — 종류 이름 — 카드에 적힌 그대로, 꼴이 틀린 칸이면 빈 글. 기록 · 뒤의 실행 · 창이 이 이름으로 그 일의 종류를 적는다.
                  - `Task.run_lines` — 뒤에서 하는 실행에 줄 카드의 줄 — 보고 글에 적힌 그대로의 머리 · 낱낱 뒤에 그 일의 값(`values`)을 「이름: 값」 한 줄씩. 실행이 방과 사람을 다시 찾지 않고, 답할 메일을 카드의 근거 메일 가운데서 짐작하지 않는다.
                  - `Task.words` — 「대화로 열기」가 VS Code 의 입력 칸에 채울 말 — 줄 · 빈 줄 · 카드의 근거. 창 곁의 손이 그 뒤에 보고 이름과 경로를 붙인다.
                - `brief_sections.report_items` — 창에 서는 줄을 창이 세우는 차례로 — 빈 「끝났다고 하신 것」 절은 창처럼 건너뛴다.
                  - `is_empty_done` — 줄이 없거나 「없음」 한 줄뿐인 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」 — 창에 안 세운다(보고 글에는 그대로 남아 다음 보고가 잇는다).
                    - `names_section` — 절 머리 `title` 이 절 `names` 가운데 하나를 이르나 — 굵게 · 링크 같은 꼴 표시를 걷은 맨글자(`plain`)로 `starts_named`. 머리가 없으면 거짓.
                      - ↑ `starts_named`
                      - ↑ `brief_inline.plain`
                - `brief_text.parse` — 보고 글을 제목 · 절 · 덩이로 가른다.
                  - `Report` — 보고 글 한 편 — 제목 · 절들 · 첫 제목 뒤에 더 나온 「# 」 제목의 수.
                    - `Section` — 보고 글의 절 하나 — 제목과 덩이들.
                      - `Block` — 보고 글의 덩이 하나 — 꼴(문단 · 목록 · 인용 · 시간줄 · 작은 절)과 그 줄 · 시간줄의 둘레 줄.
                  - ↑ `Block`
                  - ↑ `Section`
                  - `Item` — 목록 덩이의 줄 하나 — 쓴 번호 · 글 · 그 아래 줄.
                - `take_card` — 줄 하나 → (맡길 일, 앞의 점, 끝의 칸, 시각 없는 모임인가). 맡길 일의 칸을 떼고(`task_cells`) → 남은 낱낱을 점과 칸으로 가르고 → 시각 없는 모임의 칸을 떼고 → 칸마다 번호(`task_id`)와 카드의 근거(`evidence_of`)를 단 Task 를 짓는다.
                  - `task_cells` — 낱낱 → (맡길 일의 칸 (이름, 값) · 나머지 낱낱). 맡길 일의 칸은 낱낱 어디에 있어도 떼어 낸다 — 점 사이에 끼어도 글자로 남지 않게.
                  - `brief_cards.split_facts` — 낱낱을 앞의 점과 끝의 칸으로 가른다 — 끝에서부터 「이름: 값」 꼴이 이어지는 데까지가 칸이다.
                  - `brief_put.no_time_of` — 끝의 칸에서 「시각: 메일에 없음」을 떼어 낸다 — (시각 없는 모임인가, 남은 칸).
                    - ↑ `brief_inline.plain`
                  - `brief_cards.card_name` — 카드의 이름 — 제목의 맨글자를 빈칸 하나로 이은 것.
                    - ↑ `brief_inline.plain`
                    - `card_head` — 줄 머리 → (카드 제목, 그 뒤의 때와 곳). 맨 앞 `**…**` 가 없으면 줄 전체가 제목이고 뒤는 빈 글이다.
                  - `evidence_of` — 카드의 근거 — 카드 이름(`card`)과 때 · 점 · 칸의 맨글자(메일 · 사람 · 방 링크는 번호 · 주소 · id 를 남긴다 — `with_numbers`).
                    - ↑ `brief_cards.card_head`
                    - `brief_inline.with_numbers` — 맨글자 — 메일 링크는 「보일 글 (메일 번호 …)」로, 사람 링크는 「이름 <주소>」로 남긴다.
                      - ↑ `plain`
                  - `task_of` — 칸 하나 → Task — 넣을 일정(`put_in`)과 종류의 줄 · 이름 붙은 값(`cell_row`)을 고르고, 사람 칸의 사람들(`Kind.persons`)과 사람이 읽는 칸의 말(`shown_of`)을 한 번 지어 그 줄의 셈(줄 · 무엇이 되나 · 시작 · 넘길 값)을 한 번씩 부른다.
                    - `cell_text` — 맡길 일 칸의 값에서 읽을 글 — 앞뒤 빈칸과 값을 감싼 「`」를 걷은 그대로.
                    - `put_in` — 칸 하나가 든 넣을 일정 — 넘기는 길이 일정 넣기(`VIA_PUT`)인 종류의 값: 칸 이름이 그 종류를 정하면(옛 「넣을 일정」) 칸 전체, 「바로 할 일」이면 이름 뒤의 값. 그런 칸이 아니거나 꼴이 틀렸으면 None. 창을 짓기 전의 마무리(`finish.put_row`)와 맡길 일 읽기(`task_of`)가 이 한 자리로 가른다.
                      - `brief_put.put_of` — 「일정 넣기」 칸의 값 → Put. 꼴이 아니면 None — 시각 둘 · 제목 · (곳) · 공개 범위 · (열쇠). 제목에 「 | 」가 들어도 끝에서부터 읽는다.
                        - ↑ `Put`
                      - `named_kind` — 「바로 할 일」 칸의 글(`cell_text`) → (첫 값이 이름인 종류(`task_kinds.NAMED`) · 모르는 이름이면 None, 이름 뒤의 글 · 「 | 」가 없으면 None). 넣을 일정 가리기(`put_in`)와 종류의 줄 고르기(`cell_row`)가 이 한 자리로 이름을 뗀다.
                      - ↑ `cell_text`
                    - `cell_row` — 칸 하나 → (종류의 줄, 이름 붙은 값, 추천 표). 칸 이름이 종류를 정하면(`FIELD_KINDS` — 「대화로 할 일」 · 옛 「넣을 일정」) 칸 전체가 그 종류의 값 하나이고 끝의 「| 추천」은 그 종류가 받으면(`Kind.topped`) 떼어 표로, 「바로 할 일」이면 첫 값이 이름인 종류(`named_kind`)의 값들이다.
                      - ↑ `named_kind`
                      - ↑ `task_kinds.Cells`
                    - `task_kinds.shown_of` — 이름 붙은 값 → 사람이 읽는 칸의 말. 시작이 없는 종류(꼴이 틀린 칸도)는 때가 빈 글이다 — 시작이 있으면 꼴(`span_fits`)이 이미 맞았다.
                      - ↑ `Shown`
                      - ↑ `brief_put.span_words`
                      - `room_name` — 방 칸 → 사람이 읽는 방 이름. 회의실 링크 꼴이 아니면 칸 그대로.
                        - ↑ `brief_inline.plain`
                      - `said_all` — 사람들 → 사람이 읽는 「이름 직함(덧말) · …」.
                    - ↑ `Task`
                  - `task_id` — 일의 번호 — 카드 머리 · 칸의 차례 · 칸의 글에서 낸 해시의 앞(`TASK_ID_LEN`). 같은 보고 글이면 창과 창 곁의 손이 같은 번호를 낸다.
                    - ↑ `brief_inline.plain`
              - ↑ `brief_tasks.Task`
              - `names_of` — 기록 · 다음 보고에 댈 그 일의 이름 — 「카드 n 「제목」 종류」.
              - ↑ `live_or_settled`
              - `follow` — 도는 판마다 실행의 기록을 다시 읽어 누름에 얹는다 — 바뀌었나. 넘기다 손이 죽은 누름(「넘기는 중」)은 도는 판의 목록에서 찾는다.
                - `found_or_lost` — 도는 판의 목록에서 찾은 그 누름의 판을 따르게 하고, 못 찾았으면 확인 안 됨으로 맺는다 — 넘겨졌을 수 있다.
                  - `absorb` — 실행의 기록 하나를 누름에 얹는다 — 일마다의 상태 · 때 · 결과(꼴대로 왔으면 그 칸들, 아니면 온 글 그대로) · 이어 갈 세션, 판이 끝났으면 그 끝. 아무것도 안 바꾸는 종류가 「확인 안 됨」으로 맺었으면 「못 함」이다(`readonly_end` — 종류는 기록이 되돌려 준 이름으로 읽는다).
                    - `readonly_end` — 아무것도 안 바꾸는 종류(`task_kinds.Kind.read_only`)가 「확인 안 됨」으로 끝났으면 그 일의 「못 함」 칸 — 모를 것이 없어 다시 맡겨도 된다.
                      - `task_kinds.read_only` — 기록에 남은 종류 이름이 아무것도 안 바꾸는 종류인가 — 모르는 이름 · 글이 아닌 값(손으로 고친 기록)이면 거짓(됐는지 모를 수 있다).
                        - ↑ `Kind`
                        - `never_fits` — 꼴이 틀린 칸 — 어떤 값도 맞지 않는다.
                        - `no_start` — 때가 없는 일 — 빈 글.
                        - `no_values` — 넘길 값이 없다 — 뒤의 실행에 넘기지 않는 종류다.
                        - `written_line` — 꼴이 틀린 칸의 줄 — 적힌 글 그대로.
                    - ↑ `clock.stamp`
                    - ↑ `clock.local_now`
                  - `settle_all` — 넘기려던 일을 다 그 끝으로 맺는다 — 못 넘긴 판(`REFUSED`)이거나 넘겼는지 모르는 판.
                    - `unsure_row` — 됐는지 모르는 일의 칸 — 종류는 누름이 넘길 때 적어 둔 것(`entry["kinds"]`)으로 읽고, 「못 함」으로 바꿀지는 `readonly_end` 가 가른다.
                      - ↑ `clock.stamp`
                      - ↑ `clock.local_now`
                      - ↑ `readonly_end`
                    - ↑ `clock.stamp`
                    - ↑ `clock.local_now`
                - `unattended_link.find_launch` — 그 누름의 판 — 도는 판의 목록(`handed list`)에서 `brief` 가 그 누름의 열쇠인 것. 없으면 None.
                - `follow_running` — 도는 판 하나의 기록을 다시 읽어 얹는다 — 바뀌었나. 못 읽으면 그 때를 적고, `MISSING_S` 내리 못 읽으면 남은 일을 확인 안 됨으로 맺는다.
                  - `unattended_link.show` — `handed show --id <판>` 한 번 — 그 판의 기록(답의 `id` 가 그 판일 때만), 아니면 None.
                    - `last_json` — 표준 출력의 마지막 줄의 JSON 사전 — 없거나 꼴이 아니면 빈 것.
                  - ↑ `absorb`
                  - ↑ `clock.stamp`
                  - ↑ `clock.local_now`
                  - ↑ `unsure_row`
            - ↑ `Runs.save`
          - `edge.cells` — 창에서 읽은 칸 가운데 그 머리의 것 — {열쇠의 나머지: (값 그대로, 값)}. 값이 JSON 사전이 아니면 버린다.
          - `takeable` — 맡을 누름인가 — 맡지도 맺지도 않았고, 누른 지 `brief_const.RUN_TAKE_S` 안이고, 누른 창이 그 열쇠의 창이고, 할 일이 있다.
            - `edge.pressed_at` — 누르신 때 — 이 PC 의 시각. 꼴이 아니면 None.
            - ↑ `press_page`
            - ↑ `clock.local_now`
            - ↑ `brief_files.is_window`
        - ↑ `Runs.take_one`
        - `Runs.step` — 한 걸음 — 새 누름을 맡고, 맡은 누름을 넘기고, 창이 맺은 누름을 받고, 기록 없는 누름을 맺고, `FOLLOW_S` 마다 도는 판을 따르고, 창에 적는다.
          - ↑ `Runs.take`
          - ↑ `Runs.load`
          - `Runs.launch_pending` — 이 손이 맡아 「넘기는 중」으로 둔 누름을 넘기고 기록을 쓴다 — 누름마다 기록에 남길 구절.
            - `launch` — 넘길 일을 실행에 넘긴다 — 기록에 「넘기는 중」을 남긴 뒤에 부른다(그 사이 손이 죽어도 다음 손이 그 누름을 다시 넘기지 않는다). 맡긴 일 파일을 쓰고 → `handed start` 한 번 → 그 파일을 걷고 → 답을 가른다(`take_start`).
              - `tasks_body` — 실행에 줄 맡긴 일 파일의 몸 — `brief` 에 누름의 열쇠를 실어, 끝을 못 받은 판을 도는 판의 목록에서 찾는다.
              - ↑ `settle_all`
              - `unattended_link.start` — `handed start --tasks <파일>` 한 번 — (끝 — TOOK · NOT_LAUNCHED · REFUSED · UNKNOWN, 끝 줄의 JSON). 시한을 넘긴 부름은 넘겨졌을 수 있어 UNKNOWN 이다 — 「못 띄웠다」로 읽으면 사람이 같은 일을 또 맡긴다.
                - ↑ `last_json`
              - `take_start` — `handed start` 의 끝(`unattended_link.start`)을 누름에 얹는다 — 맡았다(그 판을 따른다) · 실행을 못 띄웠다 · 실행이 못 맡는다고 했다(기록을 안 썼다) · 모른다(넘겨졌는지 도는 판의 목록에서 찾고, 없으면 확인 안 됨).
                - ↑ `absorb`
                - ↑ `settle_all`
                - ↑ `found_or_lost`
                - ↑ `unattended_link.find_launch`
            - ↑ `Runs.save`
          - ↑ `edge.cells`
          - ↑ `Runs.adopt`
          - ↑ `Runs.save`
          - `Runs.close_orphans` — 창에 맡았다고 적혔는데 기록에 없는 누름을 「못 맡김」으로 맺어 창에 적는다(`orphans`) — 맺었으면 기록에 남길 구절 하나.
            - ↑ `Runs.orphans`
          - `Runs.follow_due` — `FOLLOW_S` 가 지났으면 도는 판을 따르고(`follow` — 곧 넘길 누름은 빼고), 바뀌었으면 기록을 쓴다.
            - ↑ `follow`
            - ↑ `Runs.save`
          - `tab_write` — 창에 칸들을 적는다 — 없으면 안 부른다.
          - `want_rows` — 창에 적을 칸 — 기록이 든 누름마다 그 누름의 칸(`press_cells`)과 일마다의 칸(`task_cells`). 저장소의 값과 같은 칸은 안 적는다.
            - `press_cells` — 누름마다의 칸 — 맡은 때 · 맺었으면 그 끝(`overall`). 창의 저장소에 맺음이 적혀 있어도 판이 아직 돌면 그 맺음을 걷는다.
              - `overall` — 누름 하나의 끝 — (맺었나, 끝, 맺은 때). 제가 넘긴 판과 따르는 판이 다 맺어야 맺는다.
                - ↑ `clock.stamp`
                - ↑ `clock.local_now`
                - ↑ `records.live`
                - `latest` — 때들 가운데 가장 늦은 것 — 실행의 때(UTC)와 이 손의 때(서울)가 섞여 글자로는 못 견준다.
            - `task_cells` — 일마다의 칸 — 그 일을 든 가장 늦은 누름(창의 저장소에 있는 것)의 끝.
              - ↑ `records.task_outcome`
        - ↑ `Runs.launch_pending`
        - ↑ `Runs.close_orphans`
        - ↑ `Runs.follow_due`
      - `run_unattended` — 사람 없는 실행의 명령 한 번(`unattended/<args[0]> <args[1:]> --dir <사용자 폴더>`) — (종료 값, 표준 출력). 못 띄웠거나 입구가 없으면 (None, ""), 시한을 넘겼으면 (`unattended_link.TIMED_OUT`, "") — 그 프로세스는 끊는다.
        - `proc_base.python_argv` — 곁의 파이썬 스크립트를 지금 파이썬으로 부르는 명령줄 — `-X utf8 -I`(UTF-8 · 사용자 자리의 모듈을 안 싣는다).
        - `piped` — 곁의 파이썬 손 한 번을 기다려 출력을 받는 `Popen` 인자 — 창 없이 · UTF-8 로(`proc_base`), 표준 입력은 닫고 출력 · 오류는 받는다.
          - `proc_base.utf8_env` — 띄운 파이썬이 출력을 UTF-8 로 내게 하는 환경 — 지금 환경에 `PYTHONIOENCODING` 만 얹는다.
          - `proc_base.quiet` — 창 없는 실행(작업 스케줄러의 pythonw)에서 띄운 손 · 손이 띄우는 node 가 콘솔 창을 안 띄우게 하는 `subprocess` 인자 — 창 없는 콘솔을 준다.
        - `wait_out` — 그 프로세스가 끝나기를 기다려 표준 출력을 낸다 — 시한을 넘기면 끊고 None. 기다리는 동안 `WAIT_STEP_S` 마다 `ticker` 를 부른다 — 창 곁의 손이 오래 걸리는 부름 사이에도 숨 표를 적고 맡긴 일의 끝을 받는다(안 적으면 창이 손을 없다고 읽어 도는 일을 「못 끝냄」으로 맺는다).
      - `Hand.tend` — 걸음 하나 — 숨 표를 적을 때면 적고, 새로 맡긴 누름을 맡고, 도는 판의 끝을 창에 적는다(맡는 걸음 안에서 다시 불리면 새 누름만 맡는다).
        - `beat_row` — 창 곁의 손이 살아 있다는 숨 표 한 줄 — 창은 `brief_const.HAND_BEAT_S` 의 세 배 넘게 이것이 없으면 손이 없다고 본다.
          - ↑ `clock.stamp`
          - ↑ `clock.seoul_now`
        - ↑ `log`
        - ↑ `edge.EdgeGone`
    - ↑ `edge.Cdp`
    - ↑ `edge.port`
    - `edge.brief_tabs` — 열린 보고 창 — (탭, 파일 이름). file: 탭 가운데 이름이 보고 창의 꼴인 것만. 새로 열지 않는다(사람의 Edge 에 탭이 뜨면 안 된다).
      - ↑ `brief_files.is_window`
    - ↑ `edge.Tab`
    - ↑ `edge.EdgeGone`
  - `presses.round_once` — 시계 판 한 번 — 열린 보고 창에 붙어 「일정에 넣기」 누름을 거둬 맺고, 지금 모습을 그 창에 적고, 창 곁의 손이 없으면 띄운 뒤 끝 줄을 낸다(손은 그 손을 띄울 창일 때만 — `hand_wanted`). 열린 보고 창이 없으면 아무것도 안 연다.
    - ↑ `edge.connected`
    - ↑ `edge.brief_tabs`
    - `filed_tab` — 열린 보고 창 가운데 첫 것에 붙는다 — 창이 없거나 아직 다 안 섰으면 `cli.Stop`(종료 0 — 거둘 누름 없음).
      - ↑ `cli.Stop`
      - ↑ `edge.Tab`
    - `put_presses` — 창의 「일정에 넣기」 누름을 거둬 맺고 끝을 그 창에 돌려 적는다 — 끝마다의 수. 기록의 잠금을 못 쥐면(다른 손이 넣는 중) 아무것도 안 한다 — {"busy": 1}. `until`(monotonic)을 주면 그 안에 일정 손의 시한이 다 들어가는 누름만 시작한다.
      - `edge.stored` — `cells` 를 (열쇠의 나머지, 값)으로 — 남긴 때 차례.
        - ↑ `cells`
      - ↑ `oslock.OsLock`
      - `Borrow` — 단추의 일 하나가 돌려준 사내 로그인을 잠깐 빌리는 판 — 같은 스킬 시계의 명령(`clock.py lend · release` — `unattended/loan.py`)으로 묻는다.
        - `Borrow.hold_on` — 그 일이 산 세션을 쓰기 시작한다 — 시계에 쓰는 일로 적어(빌리지 않는다) 그 도중에 시계 판이 돌려주지 않게. 이 판에서 한 번만.
          - ↑ `run_unattended`
        - `Borrow.take` — 세션이 없다는 끝을 받았다 — 이 판에서 처음이면 시계에 빌리기를 청한다.
          - ↑ `run_unattended`
        - `Borrow.give` — 쓴다고 적었으면(`hold` 면 안 적었어도 — 결재 창은 사람이 그 세션의 창에서 누른다) 시계에 놓는다고 알린다 — 쓰는 일이 더 없으면 시계가 곧 돌려준다.
          - ↑ `run_unattended`
      - `records.read_ledger` — 넣은 누름의 기록 — 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `Unreadable`. 빈 것으로 읽고 그 위에 쓰면 「넣는 중」 · 「넣음」을 잃어 같은 일정을 또 넣는다.
        - ↑ `store.read_json`
      - ↑ `store.Unreadable`
      - `press_row` — 창의 저장소에서 지금 그 누름(머리 `prefix` 의 열쇠 `key`) — 없으면 None.
        - ↑ `edge.stored`
    - `Kind` — 누름 종류 한 줄 — 새 누름은 이 표의 줄 하나와 할 일 함수 하나다.
    - `collect_puts` — 창 곁의 손이 「일정에 넣기」 누름을 거두는 걸음 — 기록에 남길 한 구절(거둔 것이 없으면 "").
      - ↑ `put_presses`
      - `count_said` — 「일정에 넣기」 끝마다의 수 — 「넣음 2 · 세션 없음 1」.
    - `settle` — 누름 하나를 맺는다 — (끝, 말) · 일정 손을 부르기 직전에 누름이 사라졌으면(사람이 다시 눌러 취소했다) None. 잠금을 쥔 채 부른다.
      - `ledger_rec` — 그 열쇠의 기록 — 없거나 꼴이 아니면 None.
      - `standing` — 기록에서 본 그 누름의 형편 하나 — DEAD(잠금을 쥐었는데 「넣는 중」 — 앞 손이 넣다 죽었다) · REPLAY(같은 누름 — 누른 때가 기록의 것과 같거나 앞 — 의 맺은 끝: 창에 적은 끝이 사라져도 두 벌을 안 넣는다.
      - `close_dead` — 넣다 죽은 기록을 맺어 기록에 적고 낸다 — 들었는지 모르니: 앞서 넣은 열쇠면 그 넣음으로, 아니면 「확인 안 됨」으로. 어느 쪽이든 죽은 그 누름은 다시 안 부른다(넣고 죽었으면 두 벌). 못 쓰면 OSError.
        - ↑ `clock.stamp`
        - ↑ `clock.seoul_now`
        - `records.write_ledger` — 새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다.
          - ↑ `clock.stamp`
          - ↑ `clock.seoul_now`
          - ↑ `store.replace`
      - `replay_end` — 맺은 기록의 끝 — (끝, 말).
      - `card_for` — 누름이 가리키는 카드 — 누른 창(`brief` — 그 창의 파일 이름)의 보고 글(`store.page_brief`)에서 그 열쇠의 카드. 글 · 카드가 없으면 None.
        - ↑ `store.page_brief`
        - `brief_tasks.cards_of` — 보고 글에서 누를 수 있는 「일정 넣기」(`pressable_put`)를 든 카드 — {열쇠: (Put, 카드의 맨글자)}. 거두는 손이 누름을 이 글의 카드에 대어 그 값으로 넣는다 — 창이 사람에게 보인 글과 같은 글이다.
          - ↑ `brief_put.Put`
          - ↑ `brief_sections.report_items`
          - ↑ `brief_text.parse`
          - ↑ `take_card`
          - `pressable_put` — 맡길 일이 든 넣을 일정 가운데 누를 수 있는 것 — 창을 짓기 전에 미리 보기의 열쇠를 받은 것(`Put.key`). 넣을 일정이 없거나 열쇠가 없으면 None. 창의 넣기 단추(`row_shape`)와 거두는 손의 카드 찾기(`cards_of`)가 이 한 자로 가른다.
          - ↑ `brief_inline.plain`
      - `put_verdict` — 넣기 전에 맺을 끝 — 카드를 못 찾았으면 못 넣음, 지난 약속이면 지난 약속, 넣을 것이면 None. 시작은 일정 넣기 종류의 시작(`CAL.start`)이다 — 창의 늦음 잠금이 읽는 줄의 시작(`brief_tasks.Task.start`)과 같은 자.
        - ↑ `brief_put.put_moment`
        - ↑ `task_kinds.Cells`
        - ↑ `clock.seoul_now`
      - `enter` — 「넣는 중」을 기록에 굳힌 뒤 일정 손을 한 번 부른다 — (끝, 말). 기록을 못 쓰면 OSError — 부르는 쪽이 일정 손을 안 부르고 멈춘다.
        - ↑ `clock.stamp`
        - ↑ `clock.seoul_now`
        - ↑ `records.write_ledger`
        - `run_calendar` — 일정 손 한 번 — 넣기(카드의 값과 열쇠 그대로), `preview` 면 같은 값의 미리 보기(일정을 안 바꾼다 — 그 판과 열쇠를 받는다.
          - ↑ `proc_base.python_argv`
          - ↑ `piped`
          - ↑ `wait_out`
        - `outcome` — 일정 손의 끝 → (끝, 사람에게 할 말). 들었는지 모르는 끝(시한 · 손 오류 · 모르는 답)은 다 「확인 안 됨」이다 — 다시 넣으면 두 벌이 든다.
          - `clock.moment_words` — 사람이 읽는 때 — 「M/D HH:MM」.
          - ↑ `clock.seoul_now`
          - `moved_words` — 그 사이 바뀜의 말 — 지금 판의 겹침 가운데 카드에 안 보였던 일정을 짚는다.
      - `record_end` — 끝을 기록에 적고 창에 돌려 적을 끝을 낸다.
        - ↑ `records.write_ledger`
        - ↑ `clock.stamp`
        - ↑ `clock.seoul_now`
    - ↑ `state.row`
    - ↑ `cli.say`
    - `round_words` — 시계 판의 끝 줄 — 「일정에 넣기」의 끝마다의 수(없으면 「거둘 누름 없음」), 창 곁의 손을 다시 띄웠으면 그 말.
      - ↑ `count_said`
    - `rehand` — 열린 보고 창 가운데 하나라도 창 곁의 손을 띄울 창이면 손을 띄운다(이미 돌면 안 띄운다 — `start_hand`) — 그 답, 안 띄울 창뿐이면 None.
      - `state.schedule_of` — 사용자 폴더의 보고 시각표에서 (걸린 보고 시각표, 건 때) — 안 걸렸거나 못 읽으면 (None, "").
        - ↑ `schedule_from`
        - ↑ `read_json`
      - `asks.ready` — 부탁을 열 수 있는 PC 인가 — 등록된 VS Code 와 그 Claude Code 확장이 있다.
        - `vscode_exe` — 등록된 `vscode:` 처리기의 실행 파일(`"…\Code.exe" --open-url -- "%1"` 의 첫 칸) — 없거나 그 파일이 없으면 None.
        - `has_extension` — VS Code 확장 폴더에 Claude Code 확장(`EXTENSION_ID`)이 깔렸나.
          - `extension_dir` — VS Code 가 확장을 찾는 자리 — VS Code 가 고르는 차례 그대로: `VSCODE_EXTENSIONS` · 홈의 `.vscode/extensions`. 설치판(사용자 · 모든 사용자 설치 — 등록된 `vscode:` 처리기가 서는 판)은 휴대 판의 값(VSCODE_PORTABLE)을 안 읽는다.
      - `hand_wanted.hand_wanted` — 창 곁의 거두는 손을 띄울 창인가 — 「일정 넣기」 카드가 있거나, 맡길 일이 있거나, 보고가 걸려(`scheduled`) 「보고 맞추기」에 「자리 밖에서 보기」 단추가 서거나, 창 머리에 「비서에게 부탁하기」 칸이 서거나(`ask_ready`), 「결재 창 열기」 단추가 서는(결재 문서 링크) 창.
        - ↑ `brief_tasks.cards_of`
        - `brief_inline.approvals_in` — 글에 링크로 선 결재 문서 id 들(쓴 차례 · 겹침 없이) — `\[글\](approval:<id>)` 가운데 id 의 꼴인 것만(굵게 · 절 표지의 이름 속도 — 창이 거기서도 단추를 짓는다). 창 곁의 손은 이 목록에 든 문서의 창만 띄운다.
        - ↑ `brief_tasks.tasks_of`
      - ↑ `store.page_brief`
      - `start_hand` — 창 곁의 손을 띄운다 — True 띄웠다 · False 이미 돈다(그 손이 잠금을 쥐고 있다) · None 못 띄웠다.
        - ↑ `oslock.OsLock`
        - ↑ `proc_base.python_argv`
        - `detach.detached_tries` — 떼어 띄우는 인자를 시도할 차례 — 부른 손이 든 작업 묶음(job)이 닫혀도 살게 묶음 밖으로 먼저, 묶음이 안 놓아 주면(`OSError`) 묶음 안에서라도 띄운다.
          - `detached` — 떼어 띄우는 `Popen` 인자 — 창 없이, 부른 프로세스와 다른 묶음으로 띄워 부른 쪽이 끝나도 띄운 것이 산다.
            - ↑ `proc_base.quiet`
    - ↑ `edge.NoEdge`
    - ↑ `cli.Stop`
    - ↑ `edge.EdgeGone`
  - `window_door.door` — `--times-done` · `--away-done` — 열린 보고 창에 붙어 그 칸을 읽고 지금 모습을 적은 뒤, 시계가 받았나를 `kind` 의 칸에 돌려 적고 한 일의 줄을 낸다.
    - ↑ `edge.window`
    - ↑ `edge.stored`
    - ↑ `state.row`
    - ↑ `cli.say`
    - `write_back` — 시계가 받았나를 그 창의 그 칸에 돌려 적는다(`kind.back`) — 그 칸이 시계가 받은 고름(같은 고른 때)일 때만. 낸 것은 한 일의 한 줄.
    - ↑ `edge.NoEdge`
    - ↑ `edge.port`
    - ↑ `edge.NoWindow`
    - ↑ `edge.EdgeGone`
  - `gather` — 거두기 — 맞춤 읽기 → 창의 표시 옮기기 → 돌아온 것 → 열린 창에 알리기 → 보고가 읽을 무리 → 끝 줄. 종료 값은 표시 옮기기의 것.
    - ↑ `prefs_file.read`
    - ↑ `cli.say`
    - ↑ `prefs_file.path_of`
    - `collect` — 창의 표시를 가장 늦은 보고 글과 맞춤 파일에 옮기고, 옮긴 표시에 남긴 때를 적는다 — (종료 값, 끝 줄). 보고 글과 맞춤 파일을 다 쓴 뒤에만 창에 적는다 — 그 사이에 멈추면 다음 판이 다시 옮기고, 보고 글에 든 번호는 더하지 않는다.
      - `latest_brief` — 가장 늦은 보고 글 — 없으면 `cli.Stop`(종료 0 — 창이 선 적이 없으니 표시도 없다).
        - ↑ `brief_files.kept_briefs`
        - ↑ `cli.Stop`
      - ↑ `edge.window`
      - `window_of` — 표시를 읽을 창 — 보고 글 곁의 창 파일, 없으면 보고 글(열린 file: 탭이 없을 때 뒤 탭으로 열 자리).
      - `waiting_marks` — 창의 칸 → (꼴에 맞는 표시, 아직 안 거둔 표시, 아직 안 거둔 「다시 넣기」).
        - `ticks_of` — 창에서 읽은 (열쇠, 값) 가운데 꼴에 맞는 누름 표시만 — (메일 번호, 값). 열쇠의 메일 번호가 32자리가 아니거나 값이 꼴이 아니면 버린다.
          - ↑ `edge.stored`
          - `mark_of` — 표시가 무엇을 누르신 것인가 — `mark`, 옛 표시는 done 이 거짓이면 open · 그 밖은 done. 꼴이 아니면 "".
        - ↑ `edge.stored`
      - `brief_text` — 가장 늦은 보고 글의 글 — 못 읽으면 `cli.Stop`.
        - ↑ `cli.Stop`
      - `sort_marks` — 표시를 나눠 보고 글의 두 절을 고친 글과 맞춤의 바뀜을 짓는다(`prefs` 를 고친다) — 두 절에 이미 든 번호 읽기 → 표시마다 한 갈래 (`take_mark`) → 「다시 넣기」 → 두 절 고치기(`folded`). 표시는 메일 번호마다 하나다(창의 저장소 열쇠).
        - `record_keys` — 보고 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에 이미 든 줄의 첫 메일 번호.
          - `brief_sections.section_keys` — 보고 글의 절 `name` 에 든 줄들의 열쇠(`row_keys`). 절이 없으면 빈 것.
            - `section_span` — 글 줄들에서 절 `name` 의 자리 — (머리 줄, 그 절이 끝나는 줄(다음 같은 층 이상의 머리 · 없으면 끝)). 머리(## · ###)가 그 이름으로 시작하는 첫 절이다.
              - ↑ `names_section`
            - `row_keys` — 줄들의 열쇠 — 줄마다 첫 메일 번호(창의 상자와 같다). 둘째부터의 번호는 근거일 뿐이라 열쇠가 아니다 — 그 번호의 표시가 남의 줄을 건드리지 않는다.
              - `brief_inline.first_unid` — 글에서 처음 걸린 메일 번호(대문자) — 링크로 서는 `\[글\](mail:<번호>)` 만 센다(굵게 속도). 고정 글자 속 · 번호 꼴이 아닌 것은 안 센다.
        - `Sorted` — 표시를 나눈 끝 — 고친 보고 글 · 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에 더할 줄 · 그 절에 이미 들어 안 더한 수 · 끝났다 · 푼 · 맞춤 파일로 간 번호 · 맞춤 파일로 간 갈래마다의 수.
        - `take_mark` — 표시 하나를 그 갈래로 얹는다(`done` · `prefs` 를 고친다) — 끝났다는 표시는 「끝났다고 하신 것」에(그 절에 이미 들었으면 세기만), 푸신 표시는 「안 끝났다고 하신 것」에, 미루거나 올리지 말라신 일은 맞춤 파일로(「끝났다고 하신 것」에서 걷힌다 — 뒤에 누르신 것이 이긴다), 되돌리신 표시는 맞춤 파일에서 걷는다.
          - ↑ `mark_of`
          - `when_of` — 누르신 때 — 이 PC 의 시각으로 「M/D HH:MM」. 꼴이 아니면 빈 글.
            - ↑ `edge.pressed_at`
            - ↑ `clock.moment_words`
          - `title_of` — 보고 글 한 줄에 설 일 이름 — 줄바꿈 · 꼴 표시를 걷고 길이를 줄인다.
            - ↑ `prefs_file.clean`
          - ↑ `edge.pressed_at`
          - ↑ `clock.local_now`
          - `prefs_file.drop_unid` — 그 메일의 줄을 세 절(보고에서 빼는 것 · 내일 다시 볼 것 · 다시 올린 것)에서 다 걷는다 — 걷은 것이 있으면 True.
            - ↑ `unid_of`
          - ↑ `prefs_file.put_later`
          - ↑ `clock.day_words`
          - ↑ `prefs_file.put_quiet`
        - `prefs_file.forget` — 「보고에서 빼는 것」에서 열쇠 `k` 의 줄을 걷는다 — 걷은 줄이나 None.
          - ↑ `key`
        - `folded` — 보고 글의 두 절을 고친 글 — 끝났다는 줄을 더하고 푼 · 맞춤 파일로 간 번호의 줄을 걷고, 푼 줄을 더하고 끝났다는 번호의 줄을 걷는다.
          - `brief_sections.fold` — 보고 글의 절 `name` 에서 열쇠(`row_keys`)가 `drop` 에 든 줄을 걷고 끝에 `lines` 를 더한 글. 걷을 것도 더할 것도 없으면 글 그대로다.
            - ↑ `section_span`
            - ↑ `row_keys`
            - ↑ `brief_inline.first_unid`
      - `write_brief` — 고친 보고 글을 바꿔 끼운다 — 안 바뀌었으면 안 쓴다.
        - ↑ `store.replace`
        - ↑ `cli.Stop`
      - `write_prefs` — 맞춤 파일을 쓴다 — 세 절이 그대로면 안 쓴다.
        - ↑ `prefs_file.write`
        - ↑ `cli.Stop`
        - ↑ `prefs_file.path_of`
      - ↑ `cli.say`
      - `stamp_window` — 거둔 표시에 남긴 때를 창에 적는다 — 다시 옮기지 않게. 못 적으면 경고 한 줄(보고 글에 든 번호는 다음 판이 다시 더하지 않는다).
        - ↑ `clock.stamp`
        - ↑ `clock.local_now`
        - ↑ `edge.EdgeGone`
      - `collected_words` — 거둔 끝 줄 — 더한 수 · 이미 든 수 · 옮긴 푼 표시 · 맞춤 파일로 옮긴 갈래마다의 수.
      - ↑ `prefs_file.path_of`
      - ↑ `cli.Stop`
      - ↑ `edge.NoEdge`
      - `no_edge` — 로그인 Edge 에 못 닿은 끝 — 종료 3 과 그 말.
      - ↑ `edge.port`
      - ↑ `edge.EdgeGone`
    - `due_back` — 「내일 다시」 줄 가운데 돌아올 날이 온 것을 「다시 올린 것」으로 옮기고 그 보고가 실었으면 걷는다(`prefs_file.take_due` — 보고 글 이름의 때로 잰다) — (돌아온 것, 아직 미룬 것, 경고). 바뀌었으면 맞춤 파일에 적는다.
      - ↑ `brief_files.kept_briefs`
      - `prefs_file.take_due` — (돌아온 줄, 아직 미룬 줄) — 돌아오는 날이 오늘이거나 지난 줄(날이 꼴이 아닌 줄도 — 미룬 채 잊히지 않게)은 「다시 올린 것」으로 옮기고 그 때를 붙인다.
        - `back_at` — 다시 올린 줄의 그 때(이 PC 의 시각) — 꼴이 아니면 None.
        - ↑ `due_of`
      - ↑ `clock.wall_now`
      - ↑ `brief_files.made_of`
      - ↑ `prefs_file.write`
    - ↑ `state.sync`
    - `report_reads.report_lines` — 보고가 읽을 무리 셋 — 맞춤, 지난 보고 뒤의 「일정에 넣기」, 지난 보고 뒤의 맡긴 일. 없는 무리는 안 선다.
      - `latest_made` — 가장 늦은 보고 글을 지은 때(이 PC 의 시각 — 그 이름이 든다) — 보고 글이 없으면 None.
        - ↑ `brief_files.kept_briefs`
        - ↑ `brief_files.made_of`
      - `summary` — 보고를 짓는 쪽이 읽을 맞춤 — 보고에서 빼는 것 · 돌아온 것 · 미룬 것(없는 무리는 안 선다).
      - `put_lines` — 지난 보고 뒤 창에서 누르신 「일정에 넣기」의 끝 — 보고 글이 없으면 빈 목록, 기록을 못 읽으면 그렇다는 한 줄.
        - `puts_since` — 넣은 누름의 기록 가운데 `made` 뒤의 것 — 맺은 때 차례. 이름의 때는 이 PC 의 시각이라 기록과 같은 서울 꼴로 바꿔 견준다.
          - ↑ `clock.stamp`
          - ↑ `records.read_ledger`
        - `put_words` — 누름마다 「제목」 시각 — 끝의 말. 없으면 빈 목록.
      - `run_lines` — 지난 보고 뒤 창에서 맡기신 일마다 그 끝 — 보고 글이 없으면 빈 목록, 기록을 못 읽으면 그렇다는 한 줄.
        - `runs_since` — 맡긴 일의 기록 가운데 `made` 뒤에 맡은 누름의 일마다 (이름, 끝의 상태, 결과 첫 줄) — 같은 일은 가장 늦은 누름의 끝 하나. 끝이 아직 없으면 판이 도는 동안은 「하는 중」. 결과가 값뿐이면(회의실 따위) 그 값이 무엇을 했나를 첫 줄로 댄다.
          - ↑ `clock.stamp`
          - ↑ `records.read_runs`
          - ↑ `records.task_outcome`
          - ↑ `records.live`
        - `run_words` — 일마다 「이름 — 끝 · 결과 첫 줄」. 없으면 빈 목록.
- `main` — 명령 입구 — 받은 길(가장 늦은 보고 · 메일 한 장 · 창 짓기)을 그 손에 나눈다.
  - `parser` — 인자 — 모델의 길(짓기)과 프로그램이 부르는 문(`--sheet` · `--slot` · `--latest`)을 `--help` 의 다른 절에 둔다.
    - ↑ `cli.Once`
  - `latest_main` — `--latest` — 가장 늦은 보고 글의 자리와 지은 때를 JSON 한 줄로 낸다(없으면 `{}`). 아무것도 안 쓴다.
    - ↑ `cli.say`
    - ↑ `brief_files.kept_briefs`
    - ↑ `brief_files.made_of`
  - `sheet_main` — `--sheet` — 사용자 폴더의 보고 글 한 장(이름 하나 · 보고 글의 꼴)에서 메일 한 장을 지어 표준 출력에 JSON 으로 낸다.
    - `sheet_made` — `--sheet` 가 받은 이름이 보고 글(이름 하나 · .md · 보고 글 이름의 꼴)이면 그 지은 때 — 아니면 `cli.Stop`.
      - ↑ `brief_files.made_of`
      - ↑ `cli.Stop`
    - `sheet_text` — 사용자 폴더의 그 보고 글 — 없거나 못 읽으면 `cli.Stop`. 거두는 손이 그 글을 바꿔 끼우는 순간이면 `read_bytes` 가 다시 해 본다.
      - ↑ `store.read_bytes`
      - ↑ `store.Unreadable`
      - ↑ `cli.Stop`
      - `decode` — 받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949. 같은 몸이 스킬 mailbox-work 의 `work.py` · mailbox-tidy 의 `journal_io.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다).
    - `titled` — 글에 제목(맨 위 「# …」)이 있나 — 없으면 그 까닭(`why`)으로 `cli.Stop`.
      - ↑ `brief_text.parse`
      - ↑ `cli.Stop`
    - ↑ `cli.Stop`
    - ↑ `cli.say`
    - `render_mail.mail_sheet` — 보고 글 한 장 → 메일 한 장 {subject, html, text}. 창과 같은 글을 같은 꼴 읽기(`parse`)로 읽어 같은 사실을 다 싣고, 빈 「끝났다고 하신 것」은 창처럼 뺀다.
      - ↑ `brief_text.parse`
      - `mail_plain` — 평문 짝의 한 줄 — 꼴 표시를 걷은 맨글자(메일 링크는 그 글만).
        - ↑ `brief_inline.plain`
      - `mail_inline` — 줄 안 — 메일의 겉(`MailSkin`)으로. 창과 같은 걸음(`inline_walk`)이 같은 꼴을 읽는다.
        - `render_base.inline_walk` — 줄 안의 꼴을 왼쪽부터 읽어 겉(`skin` — 창 · 메일)으로 짓는다: 고정 글자 · 메일 링크 · 사람 · 회의실 · 결재 문서 · 표지 · 굵게. 꼴 밖의 글과 꼴이 아닌 표시(번호가 아닌 mail: · 빈 표지)는 이스케이프해 쓴 그대로 둔다.
        - `MailSkin` — 메일의 겉 — 메일 프로그램은 <style> 을 거르므로 꾸밈은 줄마다의 style 속성에 든다.
          - `MailSkin.inside` — 링크 글 속에 쓸 겉 — 메일의 겉은 링크가 없어 그대로다.
          - `MailSkin.code` — 고정 글자 — 글만.
          - `MailSkin.bad_ref` — 꼴이 틀린 메일 표시를 안 센다 — 메일 한 장은 그 수를 안 댄다.
          - `MailSkin.mail` — 메일 표시 — 링크 없이 그 글만.
          - `MailSkin.person` — 사람 — 이름만.
          - `MailSkin.room` — 회의실 — 방 이름만.
          - `MailSkin.bad_approval` — 꼴이 틀린 결재 문서 표시를 안 센다 — 메일 한 장은 그 수를 안 댄다.
          - `MailSkin.approval` — 결재 문서 — 이름만(창을 띄우는 단추는 PC 의 보고 창에만 선다).
          - `MailSkin.pill` — 표지 — 줄마다의 style 속성으로 지은 둥근 표(`over` 면 넘친 표).
          - `MailSkin.bold` — 굵게 — <b> 로.
      - `mail_blocks` — 덩이를 차례대로 — 문단 · 줄 · 작은 절 · 주의 상자 · 시간줄.
        - ↑ `mail_inline`
        - ↑ `mail_plain`
        - `mail_item` — 줄 하나 — 점 · 칸 · 맡길 일이 딸리면 카드, 아니면 한 줄. 맡길 일은 종류와 사람이 읽는 줄(창의 줄과 같은 글)로 선다 — 어디서 누르나는 그 절의 머리에 선 한 줄이 댄다(`MAIL_TASK_INTRO`).
          - ↑ `brief_tasks.take_card`
          - `brief_tasks.card_shaped` — 줄이 카드로 서나 — 앞의 점 · 맡길 일 · 시각 없는 모임 가운데 하나라도 든다(아니면 한 줄). 창과 메일 한 장이 이 한 자로 가른다.
          - ↑ `mail_inline`
          - ↑ `mail_plain`
          - ↑ `brief_cards.card_head`
          - `brief_tasks.asks_time` — 카드에 시각을 여쭙는 말(`render_base.NO_TIME_SAID`)이 서나 — 시각 없는 모임이고 맡길 일이 없다(있으면 그 일의 줄이 선다).
          - `brief_tasks.dated_card` — 카드가 약속의 카드인가 — 맡길 일 가운데 때가 든 종류(`Kind.dated`)로 읽혔거나 칸 이름이 때가 든 종류를 정한 칸(옛 「넣을 일정」 — 꼴이 틀렸어도)이 있거나, 시각 없는 모임이다.
      - ↑ `brief_sections.is_empty_done`
      - `task_section` — 맡길 일이 든 절인가 — 그 절의 머리에 어디서 맡기나를 한 줄 세운다.
        - ↑ `brief_tasks.take_card`
  - `slot_of` — `--slot` 의 값 → (그 시각 HH:MM, 그 날) — 꼴이 아니면 ("", None).
  - `build_main` — 창 짓기 — 받은 글 → 제목 · 폴더 → 마무리 → 그리기 → 두 파일 → 경고 → 띄우기 → 끝 줄. 멈추면 그 까닭 한 줄과 종료 1.
    - `received` — 받은 보고 글 — `--in` 의 파일, 없으면 표준 입력을 글로 풀고 줄끝을 「\n」으로 맞춘다.
      - ↑ `cli.Stop`
      - ↑ `decode`
    - ↑ `titled`
    - `folder_of` — 창과 보고 글을 남길 사용자 폴더 — 없으면 `cli.Stop`(없는 폴더는 만들지 않는다).
      - ↑ `cli.Stop`
    - `finished` — 받은 글을 마무리한다(`finish.finish` — 지난 보고의 기록 절 · 「일정 넣기」의 열쇠) — (마무리한 글, 경고). 지난 보고 글을 못 읽으면 `cli.Stop` — 그 글의 기록 절을 잇지 못한 새 글이 그 자리를 덮으면 사용자가 정하신 것이 사라진다.
      - `finish.finish` — 모델이 쓴 보고 글 → (마무리한 글, 끝 줄 앞에 낼 경고). `preview` 는 일정 손을 부르는 손(시험이 갈아 끼운다).
        - `keep_declined` — 지난 보고 글만 「걸지 않기로 하셨다」는 말씀을 든 옛 꼴이면 맞춤 파일에 옮긴다 — 새 보고 글이 가장 늦은 글이 되는 이 순간이 지나면 그 말씀이 어디에도 안 남는다.
          - ↑ `prefs_file.read`
          - ↑ `prefs_file.write`
        - `carry` — 지난 보고 글의 기록 절 둘을 새 글에 잇는다 — 새 글에 이미 든 줄(같은 첫 메일 번호 · 번호가 없으면 같은 글)은 다시 안 넣는다.
          - ↑ `brief_files.kept_briefs`
          - ↑ `store.read_bytes`
          - ↑ `store.Unreadable`
          - `Unread` — 지난 보고 글이 있는데 못 읽었다 — 기록 절을 잇지 못한 새 글이 가장 늦은 글이 되면 사용자의 말씀이 사라진다.
          - `closed` — 업무 파일 「끝난 일」 절에 든 메일 번호(큰 글자) — 줄에 번호가 여럿이면 다 든다.
            - ↑ `store.read_bytes`
            - ↑ `store.Unreadable`
            - `brief_sections.section_rows` — 절 `name` 의 줄 — 빈 줄과 「없음」 줄을 뺀 그대로. 절이 없으면 빈 것.
              - ↑ `section_span`
          - ↑ `brief_inline.first_unid`
          - ↑ `brief_sections.section_rows`
          - ↑ `brief_sections.fold`
          - ↑ `brief_sections.section_span`
        - `stamp_puts` — 열쇠 없는 「일정 넣기」 줄마다 미리 보기를 한 번 불러 열쇠를 달고 그 시각의 지금을 카드의 점으로 넣는다.
          - `put_row` — 카드의 낱낱 한 줄이 「일정 넣기」 칸이면 (그 값, 칸 이름) — 아니면 (None, "").
            - ↑ `brief_tasks.put_in`
          - `preview_end` — 미리 보기 한 번의 끝 — (READY · ALREADY · UNSEEN, 받은 열쇠). 꼴에 맞는 열쇠를 「ready」로 받은 것만 READY 다.
          - `keyed_row` — 「일정 넣기」 줄 끝에 열쇠를 단다 — 값을 「`…`」로 싸 쓴 줄은 열쇠도 그 안에.
          - `drop_points` — 「일정 넣기」 줄 `i` 의 카드에서 마무리가 넣은 그 시각의 점을 걷는다 — 걷은 줄 수(그 줄 앞에 있던 것).
          - `point_at` — 「일정 넣기」 줄 `i` 의 카드에서 점을 넣을 자리 — 그 카드의 낱낱 가운데 처음 선 칸(「이름: 값」) 앞. 카드의 점이 칸보다 앞에 서야 창이 끝의 칸을 칸으로 읽는다.
          - `sub_row` — 그 줄과 같은 들여쓰기의 낱낱 한 줄.
          - `point_words` — 카드에 넣을 그 시각의 점 — 받은 판의 지금 · 이미 있음 · 못 봄.
            - `now_words` — 미리 보기 판의 그 시각 — 겹치는 일정이 없으면 「비어 있습니다」, 있으면 「HH:MM–HH:MM 제목」을 잇는다.
              - ↑ `brief_inline.plain`
      - ↑ `finish.Unread`
      - ↑ `cli.Stop`
    - ↑ `brief_text.parse`
    - `render.Ink` — 줄 안을 짓는 손 — 메일함 주소를 들고, 지은 링크 · 링크로 못 지은 메일 번호 · 번호 꼴이 아닌 mail: 표시 · 누름 단추 무리를 세고, 사람을 댄 줄(`WAIT_ME` · `WAIT_THEM`)을 모은다 — (칸 이름, 주소, 이름, 줄의 닻, 일 이름, 기한 지남 표지).
      - `Ink.mail` — 메일 링크 하나 — 메일함 주소가 있으면 웹메일에서 그 메일을 여는 링크(링크 수를 센다), 없으면 글 곁에 메일 번호(못 이은 수를 센다).
      - `Ink.inline` — 줄 안 — 창의 겉(`WindowSkin`)으로. `links` 가 거짓이면 링크 · 표 없이 글만 짓는다(링크 글 속 · 왼쪽 목록 · 창의 이름).
        - ↑ `render_base.inline_walk`
        - `WindowSkin` — 창의 겉 — 메일 링크는 웹메일에서 그 메일을 여는 링크(`Ink.mail` 이 센다), 사람 · 회의실은 이름이 서고 주소 · id 는 올리면 보이는 표, 표지는 둥근 표, 굵게는 <strong>. `links` 가 거짓이면 링크 · 사람 · 회의실의 겉 없이 글만 — 같은 글을 링크 없이 한 번 더 짓는 자리라 번호가 아닌 mail: 표시도 안 센다.
          - ↑ `Ink`
          - `WindowSkin.inside` — 링크 글 속에 쓸 겉 — 같은 창의 겉에서 링크 · 사람 · 회의실의 겉을 뺀 것.
            - ↑ `WindowSkin`
          - `WindowSkin.code` — 고정 글자 — <code> 로.
          - `WindowSkin.bad_ref` — 꼴이 틀린 메일 표시 하나를 센다 — 링크를 짓는 판에서만.
          - `WindowSkin.mail` — 메일 표시 — 링크를 짓는 판이면 웹메일 링크(`Ink.mail`), 아니면 글만.
          - `WindowSkin.person` — 사람 — 이름에 주소를 올리면 보이는 표로, 링크 없는 판이면 이름만.
          - `WindowSkin.room` — 회의실 — 이름에 id 를 올리면 보이는 표로, 링크 없는 판이면 이름만.
          - `WindowSkin.bad_approval` — 꼴이 틀린 결재 문서 표시 하나를 센다 — 링크를 짓는 판에서만.
          - `WindowSkin.approval` — 결재 문서 — 이름 곁에 숨은 「결재 창 열기」 단추(창의 스크립트가 누름을 남길 수 있는 창에서만 꺼낸다)와 그 끝의 말 자리. 누르시면 창 곁의 손이 그 문서의 창을 평소 Edge 에 띄운다 — 결재 · 반려 · 상신은 사람이 그 창에서 누른다.
          - `WindowSkin.pill` — 표지 — 둥근 표로(`over` 면 넘친 표).
          - `WindowSkin.bold` — 굵게 — <strong> 으로.
    - `mailbox_of` — 꼴에 맞는 메일함 주소(끝의 / 를 뗀 것) — 없거나 꼴이 아니면 None.
    - ↑ `clock.wall_now`
    - ↑ `state.state_of`
    - ↑ `prefs_file.read`
    - ↑ `asks.ready`
    - `render.build` — 틀에 채운 HTML · 절 수 · 줄 수 — 맡길 일 미리 가르기 → 머리 → 절 → 머리 아래 패널 → 왼쪽 목록 → 끝의 막대 · 보고 맞추기 → 틀 채우기. `state` 는 창이 보이는 지금 모습(`state.state_of` — 그 `signed` 가 머리의 한 줄을 정한다), `prefs` 는 보고 맞춤, `ready` 는 이 PC 에 VS Code 의 Claude Code 가 있나(`asks.ready`) — 그리기는 사용자 폴더 · 이 PC 를 읽지 않는다.
      - `sort_tasks` — 맡길 일을 줄마다 미리 가르고(창 곁의 손이 같은 글에서 내는 번호와 같게 — `tasks_of`) 창 머리에 올릴 추천을 고른다 — `ink` 에 적고 그 추천을 낸다.
        - ↑ `brief_sections.report_items`
        - ↑ `brief_tasks.take_card`
      - `head_part` — 창 머리 — 제목 · 머리글(첫 문단) · 지은 때 · 스스로 로그인해 지은 보고의 한 줄(`signed` 의 범위 안일 때만) · 제목 밑 덩이 — 와 그 덩이의 줄 수. 지은 때는 창의 스크립트가 이보다 먼저 거둔 표시를 이 창에서 안 쓰는 기준이다(report.js).
        - ↑ `clock.stamp`
        - `signed_note` — 스캔이 세션 없이 스스로 로그인해 띄운 보고의 범위(`state["signed"]` — 로그인한 때 `at` 부터 그 보고가 글을 남길 수 있는 끝 `until` 까지) 안에서 짓는 창의 머리에 서는 한 줄. 범위 밖에 지은 창 · 적힌 범위가 없는 창에는 빈 글 — 로그인 없이 지은 보고는 그 줄을 안 든다.
        - `render_blocks` — 덩이를 차례대로 — 제목 밑의 문단은 요약 상자로 묶고, 절 머리 바로 뒤 문단은 머리말로 세운다.
          - `render_list` — 잇단 줄 — 같은 무리(카드 · 줄)와 같은 표(번호 · 「-」)끼리 한 목록으로 묶는다.
            - `render_item` — 줄 하나 — (무리, HTML). 무리는 card(점이 딸린 줄 · 맡길 일이 든 줄) · row. `tick` 이 있으면 메일 번호가 든 줄에 「끝났음」 상자를 단다.
              - ↑ `brief_tasks.take_card`
              - `tick_box` — 누름 단추 무리 — 줄의 일 열쇠(`item_key` — 「일:」 칸의 메일, 없으면 첫 메일 번호)가 열쇠다(업무 파일은 일을 그 일을 연 메일로 잇는다). 메일 번호가 없거나 결재 문서 링크가 든 줄이면 빈 글. 할 일의 줄에는 「끝났음 · 내일 다시 · 이런 건 빼기」 셋이 서고, `tick` 이 `TICK_DONE` 이면 「끝났다고 하신 것」의 줄이라 「끝났음」 하나가 눌린 채 선다(`data-done`) — 풀면 끝나지 않았다고 되돌리신 것이다.
                - `brief_cards.item_key` — 줄 · 카드가 어느 일인가 — 누름 단추의 열쇠 메일 번호(대문자). 낱낱에 「일: <메일 링크>」 칸이 있으면 그 메일, 없으면 줄의 첫 메일 링크(머리부터 낱낱 차례로). 메일 번호가 없으면 None.
                  - ↑ `brief_inline.first_unid`
                - ↑ `brief_inline.approvals_in`
                - `brief_cards.item_title` — 줄의 일 이름 — 카드면 굵은 머리, 줄이면 맨글자의 줄표(「 — 」) 앞. 줄표 뒤는 형편 · 때 · 근거라 일 이름이 아니다.
                  - ↑ `card_name`
              - `note_waits` — 사람을 댄 칸이 있으면 그 줄의 닻 이름을 주고 사람별 무리에 넣는다 — (닻 · 없으면 빈 글, 꼴이 틀린 칸의 자리). 꼴이 틀린 칸은 사람별에 안 들고 끝 줄 앞에서 경고한다(`Ink.bad_people`).
                - ↑ `brief_people.people_in`
                - ↑ `brief_cards.item_title`
              - ↑ `brief_tasks.card_shaped`
              - ↑ `brief_cards.card_head`
              - `fact_value` — 칸의 값 — 사람을 대는 칸의 꼴이 틀렸으면 쓴 글 그대로 뒤에 그렇다는 말을 단다(맡길 일의 틀린 줄과 같은 꼴).
              - `todo_block` — 카드 끝의 할 일 칸 — 줄마다 꼴을 가르고(`brief_tasks.row_shape`) → 끝 줄 앞의 경고와 창 곁의 손이 받을 일에 세고(`note_row`) → 그 꼴의 줄을 짓는다(`ROW_WORDS`). 칸이 없으면 빈 글.
                - `brief_tasks.row_shape` — 창의 할 일 줄 하나의 꼴(`ROW_…`) — 꼴이 틀린 칸은 옛 「넣을 일정」 칸인가로, 대화로 할 일은 창 머리의 추천(`top_id`)인가로, 넣을 일정이 든 일은 누를 수 있나(`pressable_put`)로 가른다.
                  - ↑ `pressable_put`
                - `note_row` — 할 일 줄 하나를 그 꼴대로 센다 — 꼴이 틀린 「넣을 일정」은 수로, 꼴이 틀린 다른 칸은 그 글 그대로(끝 줄 앞에서 경고한다), 누를 수 있는 일은 창 곁의 손이 받을 일로(그 줄의 닻과 함께).
                - `bad_row` — 꼴이 틀린 칸의 줄 — 칸 이름 · 적힌 글 그대로 · 맡길 수 없다는 말(옛 「넣을 일정」 칸이면 그 칸의 말).
                - `talk_row` — 「대화로 할 일」의 줄 — 줄 · 추천이면 그 표 · `ready`(이 PC 에 VS Code 의 Claude Code 가 있다)이면 무엇이 되나와 숨은 「대화로 열기」. `ready` 가 거짓이면 추천 표도 안 단다.
                  - `attr` — `data-…` 속성 — 값이 None 이면 뺀다.
                - `task_row` — 누를 수 있는 일의 줄 — 숨은 표시 칸 · 줄 · 무엇이 되나 · 숨은 「이것만 맡기기」(일정 넣기면 그 열쇠와 시작을 단다) · 결과 자리. 표시 칸과 단추는 창의 스크립트가 누름을 남길 수 있는 창에서만 꺼낸다(스크립트가 막혀도 누를 수 없는 단추는 안 선다).
                  - ↑ `attr`
                - `unkeyed_row` — 열쇠를 못 받은 일정 넣기의 줄 — 줄과 이 창에서는 안 넣는다는 말. 까닭은 마무리(`finish.py`)가 카드의 점으로 넣었다.
              - ↑ `brief_tasks.asks_time`
              - ↑ `brief_tasks.dated_card`
          - `render_quote` — 주의 상자 — 「- 」 줄은 목록, 그 밖은 문단(빈 「>」 줄이 문단을 가른다).
          - `render_clock` — 시간줄 덩이 하나를 HTML 로 — 줄마다 때 · 할 일 · 곁말을 세우고, 위 줄의 이름과 아래 곁말을 둘레에 단다.
      - `section_parts` — 절마다의 HTML(빈 「끝났다고 하신 것」은 안 세운다) · 끝의 기록 절이 시작하는 자리(맨 아래의 누름은 마지막 카드 뒤, 그 앞에 선다) · 줄 수. 왼쪽 목록에 절과 그 작은 절을 더한다.
        - ↑ `brief_sections.is_empty_done`
        - ↑ `brief_sections.names_section`
        - ↑ `render_blocks`
        - `section_tick` — 절의 줄에 다는 상자 — 「끝났다고 하신 것」은 눌린 것이 바탕인 상자, 다른 기록의 절은 없음, 나머지는 할 일의 상자.
          - ↑ `brief_sections.names_section`
          - `brief_sections.is_meetings` — 회의 한 장의 절인가 — 종류 표지(`MEETINGS`)가 든 머리, 표지 없이 쓴 글이면 이름이 `MEETING_SECTION` 으로 시작하는 머리.
            - `section_kind` — 절 머리의 종류 — 머리 전체가 「\[이름\](section:<종류>)」 꼴이면 그 종류, 아니면 빈 글.
            - ↑ `names_section`
      - `people_panel` — 사람별 — 같은 줄들을 사람으로 한 번 더 세운다: 나를 기다리는 분(`WAIT_ME`) · 내가 답을 기다리는 분(`WAIT_THEM`). 사람마다 그 일들로 가는 닻 링크다.
      - `head_panels` — 머리 아래의 패널 — 거둘 수 없는 창의 한 줄(단추 · 맡길 일이 서는 창만) · 부탁 칸 · 「바로 맡길 일」 막대 · 사람별(있을 때만).
        - `ask_panel` — 창 머리의 「비서에게 부탁하기」 — 칸 · 단추 · 한 줄 설명. 칸은 처음엔 숨고 그렇다는 한 줄이 선다 — 창의 스크립트가 거둘 수 있는 창에서만 칸을 꺼내고 그 줄을 숨긴다.
          - ↑ `attr`
        - `board_panel` — 머리 칸 아래의 「바로 맡길 일」 — 처음엔 접힌 막대 하나. 맡길 일이 없는 보고에는 안 선다.
          - `board_bar` — 막대의 첫 줄 — 제목 · 셈(창의 스크립트가 채운다) · 맡긴 뒤의 표지 · (위에만) 목록 펴기 · 누름.
          - `board_rows` — 편 목록의 줄 — 한 일에 한 줄(표시 칸 · 종류 · 카드 제목 · 표지 · 카드로 가는 닻). 무엇이 되나는 카드의 줄에만 선다.
            - ↑ `attr`
      - `side_list` — 왼쪽 목록의 머리 칸을 창의 차례대로 끼운다 — 머리 칸 아래의 막대가 사람별보다 위다(`toc` 를 고친다).
      - `tail_parts` — 끝의 덩이 — 맨 아래의 「바로 맡길 일」은 기록 절 앞(없으면 끝), 「보고 맞추기」는 맨 끝에 — 와 그 목록 줄(`sections` · `toc` 를 고친다).
        - `board_end` — 마지막 카드 뒤의 같은 누름 — 카드를 다 읽은 자리에서 맡긴다.
          - ↑ `board_bar`
        - `prefs_panel` — 보고 맞추기 — 보고 시각(고르시면 스캔이 받아 건다) · 보고에서 빼는 것(「다시 넣기」) · 내일 다시 볼 것. 고르는 칸은 처음엔 숨고 창의 스크립트가 표시를 거둘 수 있는 창에서만 꺼낸다 — 아닌 창은 지금 값만 보인다.
          - `away_part` — 「자리 밖에서 보기」 칸 — 켜고 끄는 단추 하나와 받는 분 · 한 줄 설명. 단추는 처음엔 숨고 창의 스크립트가 거둘 수 있는 창에서만 꺼낸다 — 아닌 창은 지금 켜졌나만 보인다.
            - `away_to` — 받는 분의 한 줄 — 켰으면 켤 때 주소록에서 받은 본인 주소. 창에는 고칠 칸이 없다.
          - ↑ `prefs_file.key`
          - `now_words` — 「M/D HH:MM」 — 창이 보이는 모습이 언제 것인가.
            - ↑ `clock.moment_words`
          - `unread_note` — 못 읽은 파일이 있을 때 「보고 맞추기」 머리에 서는 한 줄 — 비어 보이는 칸이 비어 있는 것이 아니라고 말한다.
      - `filled` — 틀(`assets/report.html`)에 창의 이름 · 왼쪽 목록 · 머리 · 절 · 스크립트와 그 CSP 해시를 채운 HTML.
        - `page_script` — 창에 싣는 스크립트와 그것만 여는 CSP 칸(`'sha256-…'`). 해시는 실을 글 그대로에서 낸다 — 손으로 옮긴 해시는 없다.
        - ↑ `brief_inline.plain`
    - `write_pair` — 창 HTML 을 쓰고, 선 뒤에만 같은 이름의 보고 글을 남긴다 — (창, 보고 글). 남은 글은 다음 보고가 사용자께 낸 보고로 읽는다.
      - ↑ `cli.Stop`
    - ↑ `cli.Stop`
    - ↑ `cli.say`
    - `brief_sections.missing_ends` — 글에 없는 끝의 절 — 절(##)이나 작은 절(###)의 머리가 그 이름으로 시작하면 있는 것으로 본다(「(2건)」 같은 덧말 · 굵게는 괜찮다).
      - ↑ `names_section`
    - `window_words.warn_lines` — 끝 줄 앞에 설 경고 · 알림 — 마무리가 낸 경고, 그리고 그린 글의 수마다 한 줄(0 이면 안 선다).
    - `brief_inline.url_count` — 글에 쓴 주소(링크로 짓지 않고 글자로 두는 것)의 수.
    - `shown_where` — 띄운 곳의 말 — `--no-open` 이면 안 띄우고, 아니면 띄운다(창 곁의 손은 그 손을 띄울 창일 때만 — `wanted`).
      - `open_report` — 보고 창을 로그인 Edge 의 새 탭에, 안 되면 기본 브라우저로 띄우고 어디에 띄웠나를 한 줄로 낸다.
        - `edge.open_tab` — 보고 창을 로그인 Edge 의 새 탭에 연다 — 열었나. 주소 꼬리(`VIA_EDGE`)를 달아, 누르신 표시가 거둬지는 창에서만 단추가 선다.
          - ↑ `port`
        - `window_words.edge_words` — 로그인 Edge 의 새 탭에 띄운 말 — 창 곁의 손을 띄울 창이면(`wanted`) 그 끝(`presses.start_hand` 의 답)도 단다.
        - ↑ `presses.start_hand`
    - ↑ `hand_wanted.hand_wanted`
    - `window_words.end_lines` — 끝 줄과 그 뒤의 「다음:」 — 지은 두 파일 · 절 · 줄 · 메일 링크 · 맡길 일의 수 · 띄운 곳, 빠진 끝의 절, 링크 없이 세운 메일.
- `main` — 보내는 손의 입구 — 표준 입력의 메일 한 장을 본인 주소로 한 통 보낸다.
  - `address_of` — 켜 둔 자리 밖에서 보기의 본인 주소 — 꺼졌거나 없으면 "". 시각표를 못 읽으면 `st.Unreadable`(안 보낸다).
    - `unattended/brief_schedule.away_of` — 걸어 둔 자리 밖에서 보기 — {on, address, chosen, set}. 안 켰으면 빈 것.
    - `unattended/brief_schedule.read_brief` — 보고 시각표 파일 그대로 — 없으면 None, 있는데 못 읽으면 `st.Unreadable`. 한 칸만 바꿔 쓰는 쪽은 이것으로 읽어 다른 칸을 옮겨 적는다.
      - `unattended/unattended_store.read_json` — JSON 한 장 — 없으면 None · 읽었으면 그 dict · 있는데 못 읽었으면 `Unreadable`(바탕이 가른 까닭과 깨짐을 옮겨 싣는다).
        - ↑ `store.read_json`
        - ↑ `store.Unreadable`
        - `Unreadable` — 파일은 있는데 못 읽었다 — 「없다」가 아니다.
  - ↑ `unattended/unattended_store.Unreadable`
  - `handed` — 중계에 글을 넘기기 시작한 뒤에 진 것인가. 중계가 거절 코드로 답했으면 안 받은 것이고, 글(DATA)을 보내기 전에 진 것도 안 간 것이다.
  - `why` — 사람이 읽는 까닭 한 구절 — 예외의 말은 안 옮긴다(거절된 주소를 든다).
- `main` — 명령 입구 — 사용자 폴더를 정하고(`--dir` · 없으면 스캔에 묻는다) 받은 하위 명령을 그 손에 나눈다.
  - `parser` — 명령줄의 꼴 — 하위 명령 · 인자 · 도움말.
  - `unattended/clock_tick.tick` — 시계 한 판 — 잠금을 못 쥐면 아무것도 안 내고 0. 쥐면 옛 파일을 옮겨 받고(`take_over`) 그날 장부를 읽어 이 판의 때를 먼저 적고(창의 `seen`), 판을 한 뒤 장부를 다시 쓰고 판 끝의 줄을 찍는다.
    - ↑ `oslock.OsLock`
    - `clock.utc_now` — 지금 — UTC.
    - `unattended/take_over.take_over` — 옛 파일 짝(`LEGACY_FILES`)과 옛 그날 장부를 옮겨 받는다 — 옮긴 새 이름들. 옛 것을 그 순간 못 읽으면 그것만 이번에 건너뛴다(다음 판이 다시 본다). 시계가 이미 돈 폴더면 빈 것. 못 쓰면 OSError.
      - `copied` — 새 파일이 없고 옛 파일이 있으면 그 바이트를 새 이름으로 바꿔 끼워 쓴다 — 옮겼으면 True.
        - ↑ `store.read_bytes`
        - ↑ `store.Unreadable`
        - ↑ `store.replace`
      - `day_taken` — 새 그날 장부가 없고 옛 지금 모습에 그날 장부 칸이 있으면 그 칸을 그대로 새 파일로 쓴다 — 옮겼으면 True. 날이 바뀐 장부여도 옮긴다(지난날 건너뛴 시각의 한 줄은 새 장부를 열 때 선다).
        - ↑ `unattended/unattended_store.read_json`
        - ↑ `unattended/unattended_store.Unreadable`
        - `unattended/unattended_store.write_json` — JSON 한 장을 바탕의 바꿔 끼우기(`store.replace`)로 쓴다 — 자리가 없으면 만든다.
          - ↑ `store.replace`
    - `unattended/clock_book.load` — 판의 상태 `{"brief": 그날 장부}` — 파일이 없거나 글이 깨졌으면 빈 상태(그날 장부는 다음 판이 새로 연다). 그 순간 못 읽었으면 `st.Unreadable` — 빈 것으로 읽어 쓰면 그날 띄운 칸을 잃어 같은 시각을 다시 띄운다.
      - ↑ `unattended/unattended_store.read_json`
      - `path_of` — 그날 장부 파일의 자리.
      - ↑ `unattended/unattended_store.Unreadable`
    - ↑ `unattended/unattended_store.Unreadable`
    - `clock.parse` — 남긴 때(시간대가 붙은 ISO 글자)를 시각으로 — 못 읽거나 시간대가 없으면 None.
    - `unattended/clock_book.clock_at` — 시계의 마지막 판 때 — 없거나 못 읽으면 "".
      - ↑ `unattended/unattended_store.read_json`
      - ↑ `path_of`
      - ↑ `unattended/unattended_store.Unreadable`
    - `unattended/clock_book.save` — 판의 상태의 그날 장부와 이 판의 때를 한 장으로 바꿔 끼워 쓴다.
      - ↑ `unattended/unattended_store.write_json`
      - ↑ `path_of`
      - `clock.utc_stamp` — 사람 없는 실행이 남기는 때 — UTC ISO 8601(초까지). 시간대 없는 시각은 받지 않는다(`ValueError`).
    - `parts_missing` — 판이 기대는 것 가운데 없는 것의 줄 — 회사 메일 손(`--hand`) · 곁의 메일함 스캔. 다 있으면 빈 것.
      - `unattended/scan_door.mail_hand` — 회사 메일 손의 자리 — 준 것(`--hand`)이 있으면 그것, 없으면 형제 스킬 company-mail 의 mail.py. 없으면 (None, 까닭).
    - `unattended/clock_round.round_lines` — 판 한 번 — 자리 밖에서 보기의 메일(`mail_step`)을 먼저 보내 그 끝이 이 판에 띄우는 보고의 부탁 글에 실리게 하고, 보고 창에서 고르신 것(`window_choices`)을 받아 걸린 시각표에 얹은 뒤 띄우기(`brief_step`)를 하고, 보고 창의 「일정에 넣기」 누름을 그 뒤에 거둔다(보고를 안 걸었어도). 누름을 거두는 데 몇 분이 들 수 있어 띄우기가 그것을 기다리지 않게 뒤에 둔다.
      - `unattended/away_mail.mail_step` — 자리 밖에서 보기 — 켠 PC 에서, 켠 뒤에 사람 없이 띄운 보고가 끝나 남긴 보고 글 한 장을 칸마다 한 통 본인 주소로 보낸다.
        - `unattended/brief_schedule.load` — (설정, 못 읽은 까닭). 안 걸었으면 (None, ""). 시각 하나(꼴 1)로 걸어 둔 설정도 읽어 `times` 를 채운다.
          - ↑ `read_brief`
          - ↑ `unattended/unattended_store.Unreadable`
          - `setting_of` — 시각표 파일 그대로(`read_brief`) → (설정, 꼴이 아닌 까닭). 없으면 (None, "").
            - `unattended/brief_slots.times_given` — 받은 시각들(빈칸 · 쉼표로 여럿도) → 정렬하고 겹친 것을 걷은 시각표. 꼴이 아닌 것이 있으면 ([], 까닭).
              - `clock` — 「H:MM」 · 「HH:MM」 → 「HH:MM」. 꼴이 아니면 None.
        - `left_sending` — 앞 판이 남긴 「보내는 중」 표지(`AWAY_SENDING_FILE`)를 맺는다 — 그 칸의 기록에 표지보다 늦은 끝이 있으면 그 판이 끝을 적은 것이라 표지만 걷고, 없으면 그 판이 중계를 부른 뒤 끝을 적기 전에 죽은 것이라 「보냈는지 모른다」로 맺는다 — 다시 보내면 두 통일 수 있다.
          - ↑ `unattended/unattended_store.read_json`
          - ↑ `unattended/unattended_store.Unreadable`
          - ↑ `clock.utc_stamp`
        - `unattended/brief_words.away_line` — 자리 밖에서 보기의 판 끝 한 줄 — 표지를 못 읽었다 · 앞 판의 표지로 칸을 맺었다 · 다음 판에 둔다 · 표지를 못 굳혔다 · 한 통 보내 봤다.
          - `mail_words` — 칸의 메일 기록의 한 구절 — 상태(`brief_state.mail_status`)를 말로. 판 끝 · status 가 같은 말을 쓴다.
            - `hhmm` — 서울 「HH:MM」 — 저장된 글자도 받는다.
              - ↑ `clock.parse`
            - `end_words` — 칸의 끝 「HH:MM」 — 그날 자정이면 「자정」.
              - ↑ `hhmm`
        - `unattended/brief_slots.seoul_date` — 서울 날짜 「YYYY-MM-DD」 — 그날 칸 장부와 보고 글 이름의 날.
          - `clock.seoul` — 시각을 서울 글자로 — 없으면 빈 글.
        - `unattended/brief_slots.noon_of` — 저장된 날짜(「YYYY-MM-DD」)의 서울 정오 — 그날의 칸을 셈할 바탕. 꼴이 아니면 None.
          - `on_day` — 서울 날짜 `at` 의 그 시각(「HH:MM」).
            - ↑ `clock`
            - `minute` — 분 단위의 때 — 틈을 분으로 잰다.
        - `send_day` — 그날(`ref` 의 날) 칸들의 메일을 맺는다 — 보낼 칸마다(`due_mails`) 한 판에 한 통까지, 판이 늦었으면 다음 판에 두고, 보낼 수 있으면 한 통 보낸다(`send_one`). 한 일을 `done` 에 더한다.
          - `due_mails` — 그날(`ref` 의 날) 칸 가운데 지금 보낼 것 — 켠 뒤에 띄웠고, 아직 맺지 않았고(다시 보낼 칸은 그 칸이 끝나기 전까지), 띄운 보고가 끝나 글을 남긴 칸(보고 글은 사용자 폴더 `folder` 에 선다). 시각표에서 빠진 칸도 띄운 기록이 있으면 끝난 칸으로 본다.
            - ↑ `unattended/brief_schedule.away_of`
            - ↑ `clock.parse`
            - `unattended/brief_slots.windows` — 그날의 칸 — 시각마다 (시각, 덮는 첫때, 시작, 끝). 끝은 다음 시각 · 그 시각에서 `BRIEF_WAIT_MIN` 분 뒤 · 그날 자정 가운데 이른 것. 덮는 첫때는 앞 칸의 끝(첫 칸은 그날 0시)이다 — 그 뒤 이 칸의 끝 전에 지은 보고 글(대화에서 지은 것도)이 이 칸의 보고다.
              - ↑ `on_day`
              - `until_given` — 검사가 준 기다림의 끝 「HH:MM」(`BRIEF_UNTIL_ENV`) — 없으면 None(시각마다 `BRIEF_WAIT_MIN` 분까지).
                - ↑ `clock`
            - `unattended/brief_reports.launches` — 그날 장부에서 띄운 칸들 — (띄운 때, 시각)을 띄운 차례로. 못 띄운 칸은 뺀다.
              - ↑ `clock.parse`
            - `unattended/brief_state.mail_status` — 칸의 메일 기록이 지금 어떤가 — 기록 없음 · 보냈다 · 칸이 끝나기 전에 넘기기 전에 진 것(판마다 다시 보낸다) · 칸이 끝나 못 보냈다 · 보냈는지 모른다(넘기는 도중 · 뒤에 졌다).
            - `unattended/brief_reports.launch_outcome` — 그날 `t` 칸이 띄운 보고가 지금 어떤가 — (WRITING, None) 아직 돈다 · (EMPTY, None) 글 없이 끝났다 · (LEFT, 글) 끝나 글을 남겼다.
              - ↑ `clock.parse`
              - `launched_end` — 그날 `t` 칸이 띄운 보고가 끝난 때(`run_end`) — 뒤 칸이 다시 띄운 때를 함께 댄다.
                - ↑ `clock.parse`
                - ↑ `launches`
                - `run_end` — 스캔이 띄운 보고 한 판이 끝난 때 — 도는 중이면 None. 뒤 칸이 다시 띄웠으면(`later`) 이 보고는 그 앞에 끝났다(출력 파일은 이제 뒤 보고의 것이다). 아니면 띄운 프로세스(`pid` · 뜬 때 `born` — 번호를 남이 받았으면 끝났다)가 끝났나로 가르고, 끝났으면 출력 파일을 마지막으로 쓴 때가 끝이다(`claude -p` 는 다 끝난 뒤에 답을 낸다) — 출력 없이 죽은 보고는 띄운 때가 끝이다.
                  - `unattended/launch_base.process_alive` — 그 프로세스가 아직 도나 — 모르면 None(번호가 없다 · 그런 프로세스가 없다는 답이 아닌 까닭으로 못 물었다 — 끝났다고 읽으면 도는 보고 곁에 하나를 더 띄운다). 뜬 때(`born` — `process_born` 이 낸 값)를 주면 그 번호의 지금 프로세스가 다른 때에 떴을 때 끝났다고 읽는다 — 바쁜 PC 는 끝난 프로세스의 번호를 몇 초 안에 남에게 준다.
                    - `_born` — 열린 프로세스가 뜬 때 — GetProcessTimes 의 첫 값. 못 물었으면 None.
                  - `last_line` — 띄운 보고의 출력에서 끝 줄 — 비었으면 "". `claude -p` 는 다 끝난 뒤에 답을 내므로, 출력이 섰으면 그 실행은 끝났다.
              - `unattended_brief` — 그 칸이 띄운 보고가 남긴 보고 글 — 띄운 때부터 그 보고가 끝난 때까지 이름의 때가 든 글 가운데 마지막(끝의 절을 더해 다시 지은 글이 뒤에 선다). 대화에서 그 뒤에 지은 글은 안 든다.
                - ↑ `clock.parse`
                - `made_between` — 사용자 폴더의 그 칸의 날 보고 글 가운데 이름의 때(서울)가 `cover` 부터 `end` 전인 것 — 이름 차례. 이름의 꼴은 이 스킬의 원본 (`brief_files.made_of` — 지은 때의 PC 시계다.
                  - ↑ `unattended/brief_slots.seoul_date`
                  - ↑ `brief_files.made_of`
                  - ↑ `unattended/brief_slots.on_day`
                - ↑ `unattended/brief_slots.on_day`
          - `late` — 이 판이 메일 한 통 · 주소록 한 번을 새로 시작하기에 늦었나 — 시작한 일이 시계 작업의 시한 안에 끝나야 한다(`AWAY_LATEST_S`).
            - ↑ `clock.utc_now`
          - `send_one` — 칸 하나의 보고를 한 통 보낸다 — 메일 한 장(`sheet_of`) → 「보내는 중」 굳히기(`mark_sending`) → 보내는 손(`send_sheet`) → 칸의 기록에 끝을 적는다.
            - `unattended/window_link.sheet_of` — 사용자 폴더의 보고 글 한 장 → 메일 한 장(보고 창 손 `window.py --sheet` 가 창과 같은 글에서 짓는다). `date` 는 그 칸이 든 날(그날 칸의 기록의 날 — 제목이 그 칸의 날을 댄다). 내는 것 — (JSON 바이트, "") 나 (b"", 까닭).
              - `proc_base.run_python` — 곁의 파이썬 스크립트 한 번 — 창 없이 · UTF-8 로 띄워 출력을 받는다.
                - ↑ `python_argv`
                - ↑ `utf8_env`
                - ↑ `quiet`
            - `mark_sending` — 중계를 부르기 전에 「보내는 중」 표지(그날 · 칸의 시각 · 때)를 굳힌다 — 그 뒤 판이 끝을 적기 전에 죽으면 다음 판이 이 표지를 본다.
              - ↑ `unattended/unattended_store.write_json`
              - ↑ `clock.utc_stamp`
              - ↑ `clock.utc_now`
            - `send_sheet` — 보내는 손 한 번 — (끝, 까닭). 넘기기 전에 진 것만 `AWAY_RETRY` 이고, 시한을 넘겼거나 모르는 끝은 다 `AWAY_UNSURE` 다.
              - ↑ `proc_base.run_python`
            - ↑ `clock.utc_stamp`
            - ↑ `clock.utc_now`
            - ↑ `unattended/brief_state.mail_status`
        - `unattended/brief_told.today` — 그날 장부를 연다 — 날이 바뀌었으면 새 장부에 지난날 건너뛴 칸의 줄(`before`)을 남긴다.
          - `unattended/brief_day.roll_day` — 그날의 살펴보기 장부 — 서울 날짜가 바뀌었으면 새 장부를 연다.
            - `migrated` — 시각 하나를 쓰던 꼴의 그날 장부 → 칸 꼴(첫 시각의 칸). 이미 칸 꼴이면 그대로.
            - ↑ `unattended/brief_slots.seoul_date`
          - `yesterday_lines` — 지난날 장부에서 보고 없이 끝난 칸의 줄 — 그날이 다 끝난 때(자정)로 재고 줄마다 그날을 단다.
            - ↑ `unattended/brief_slots.noon_of`
            - ↑ `unattended/brief_slots.on_day`
            - `unattended/brief_words.dated_lines` — 지난날의 줄 — 줄마다 그날(「M/D」)을 앞에 단다.
            - `unattended/brief_words.told_words` — 보고가 아직 말하지 않은 칸(`brief_state.untold`)의 줄 — 건너뛴 칸 · 글 없이 끝난 칸 · 못 띄운 칸, 그 앞날의 줄(`before` — 말할 차례일 때), 못 간 메일 차례로.
              - ↑ `hhmm`
              - `mail_failure_words` — 못 간 메일 한 칸의 줄 — 「HH:MM 보고는 메일로 못 보냈다 · 보냈는지 확인하지 못했다 — 까닭」.
            - `unattended/brief_state.untold` — `at` 의 날 칸 가운데 지금(`now` · 없으면 `at`) 앞에 끝났는데 보고가 아직 말하지 않은 것 — 마지막으로 보고가 선 칸 뒤의 건너뛴 칸 · 글 없이 끝난 칸 · 못 띄운 칸, 그리고 끝을 적은 뒤 띄운 보고가 아직 없는 못 간 메일. 시각표를 걸기 전에 끝난 안 살펴본 칸은 안 센다.
              - ↑ `unattended/brief_slots.windows`
              - `slot_state` — 그날(`ref` 의 날) `order` 째 칸의 상태를 지금(`now`) 한 번 셈한다.
                - ↑ `unattended/brief_slots.windows`
                - `unattended/brief_reports.reports` — 그 칸의 보고 글 — 덮는 첫때부터 끝 전에 이름의 때가 든 글에서 앞 칸이 띄운 보고가 남긴 글(그 띄운 때부터 그 보고가 끝난 때까지)을 빼고, 이 칸이 띄운 보고가 남긴 글을 더한다.
                  - ↑ `unattended/brief_slots.windows`
                  - `launched_span` — 그 시각 칸이 띄운 보고가 글을 남길 수 있던 때의 범위 — 띄운 때(분까지 — 글 이름의 때는 분까지다)부터 그 보고가 끝난 때(돌면 지금)까지. 못 띄웠거나 안 띄웠거나 띄운 때를 못 읽으면 None.
                    - ↑ `clock.parse`
                    - ↑ `launched_end`
                  - ↑ `made_between`
                - `before_set` — 그 칸이 시각표를 걸기 전에 이미 끝났나 — 그런 칸은 건너뛴 보고가 아니다(그날은 안 뜨고 다음 날부터 뜬다).
                  - ↑ `clock.parse`
                - `made_how` — 그 칸의 보고 글이 어떻게 섰나 — (MADE_SCAN, "") 스캔이 띄웠다 · (MADE_EARLY, 「HH:MM」) 칸이 열리기 전에 지은 글이 대신한다 · (MADE_IN, "") 칸 안에서 지었다.
                  - ↑ `unattended/brief_slots.on_day`
                - ↑ `unattended/brief_reports.launch_outcome`
                - ↑ `unattended/brief_reports.last_line`
                - `unattended/brief_reports.lock_held` — 시계가 띄운 보고가 도는 중이면 그 기록 — 기록에 적은 띄운 때 · 프로세스 번호와 출력(`LAUNCH_LOG_FILE`)으로 `run_end` 가 「안 끝났다」를 내면. 못 읽은 잠금은 그 파일의 고친 때를 띄운 때로 잰다(`st.held_since`) — 프로세스를 모르니 출력이 빈 동안은 돈다고 본다(못 읽었다고 안 도는 것으로 읽으면 보고를 하나 더 띄운다). 어느 쪽이든 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다.
                  - `unattended/unattended_store.held_since` — 띄운 기록 한 장(`{started, …}`) — 없으면 None. 있는데 못 읽으면 `{"started": 그 파일의 고친 때}` 로 낸다(그 때로 낡음을 잰다). 고친 때도 못 보면 지금으로 낸다 — 그 기록을 도는 것으로 둔다.
                    - ↑ `read_json`
                    - ↑ `Unreadable`
                    - ↑ `clock.utc_now`
                    - ↑ `clock.utc_stamp`
                  - ↑ `clock.parse`
                  - ↑ `run_end`
                - `unattended/brief_kinds.Slot` — 칸 하나의 셈 — 시각 · 차례 · 시작 · 끝 · 그날 장부의 칸 · 그 칸의 보고 글 · 상태 · 걸기 전에 끝난 안 살펴본 칸인가 · 띄운 보고의 출력 끝 줄(글 없이 끝난 칸만) · 보고 글이 어떻게 섰나와 칸이 열리기 전에 지은 글의 때(MADE 만).
              - ↑ `clock.parse`
              - ↑ `mail_status`
              - `skip_cause` — 끝난 칸을 왜 건너뛰었나 — 판이 안 돌았다 · 손이 세션을 못 살펴봤다 · 세션이 없고 그 칸의 스스로 로그인도 안 섰다 · 세션이 없었다.
              - `unattended/brief_kinds.Told` — 보고가 아직 말하지 않은 칸 — 마지막 보고 뒤의 칸마다 (상태, 시각, 값) · 그 앞날의 줄(`before`)도 말할 차례인가 · 못 간 메일마다 (끝을 적은 때, 시각, 메일 끝, 까닭).
      - `window_choices` — 보고 창에서 고르신 보고 시각과 「자리 밖에서 보기」를 받아 건다 — 보고가 걸려 있을 때만, 보고 창의 문 한 번(`window_door.read_choices`)으로 둘을 읽는다.
        - ↑ `unattended/brief_schedule.load`
        - `unattended/window_link.edge_listening` — 이 PC 의 로그인 Edge 디버깅 포트(`edge.port`)가 받나 — 안 받으면 보고 창을 묻는 손을 안 띄운다(판마다 프로세스 하나를 아낀다).
          - ↑ `edge.port`
        - `window_door.read_choices` — 열린 보고 창에 붙어 고르신 것을 읽고(`choices_of`) 그 창에 지금 모습을 적는다 — 시계 판이 함수로 부른다.
          - ↑ `edge.window`
          - ↑ `state.row`
          - `choices_of` — 창에서 읽은 칸에서 시계가 받을 고름 — 보고 시각 고름(`press_kinds.TIMES`)과 「자리 밖에서 보기」 고름(`press_kinds.AWAY`)을 창 곁의 손과 같은 자로, 시계 판의 때(늘 거둔다)로 잰다.
            - `Choices` — 보고 창에서 고르신 것 가운데 시계가 받을 것 — `times` (고르신 시각들, 그때 보던 시각들, 고른 때) · `away` (켬인가, 고른 때). 거둘 고름이 없는 쪽은 None.
            - ↑ `edge.stored`
          - ↑ `edge.EdgeGone`
          - ↑ `edge.NoWindow`
        - ↑ `window_door.Choices`
        - `window_times` — 보고 창에서 고르신 보고 시각(`picked` — 고르신 시각들 · 보던 시각들 · 고른 때)을 걸고(`take_window_times`), 받았나와 까닭을 그 창에 돌려 적는다 — 창 곁의 손이 없을 때의 뒷받침이다(그 손은 같은 일을 `clock.py window-times` 로 바로 한다). 내는 것 — 판 끝에 찍을 한 줄(고르신 시각이 없으면 "").
          - `unattended/brief_window.take_window_times` — 보고 창에서 고르신 보고 시각을 받는다 — 어떻게 받나를 가르고(`window_verdict`), 얹을 것이면 걸고(`apply_window`), 받은 고름의 표지를 남긴다(두 길이 같은 고름을 함께 받으면 둘째는 첫 끝을 다시 낸다). 내는 것 — (그 창에 적을 말, 걸지 않은 것이 있나).
            - `window_verdict` — 보고 창의 고름을 어떻게 받나 — (AGAIN, 그때의 말, 안 걸었나) 같은 고름을 이미 받았다 · (STALE,) 고른 뒤에 대화에서 시각을 걸었다 (나중의 말씀이 이긴다) · (BAD, 까닭) 시각의 꼴이 아니다 · (APPLY, 더하신 것, 빼신 것) 창이 보이던 시각(`seen` · 비면 지금 걸린 것)에서 더하고 빼신 것.
              - `unattended/brief_words.in_force` — 지금 걸린 시각표의 한 구절 — 거절할 때마다 함께 댄다.
              - `clock.parse_chosen` — 보고 창이 낸 고른 때(끝의 「Z」는 UTC)를 시각으로 — 못 읽으면 None.
                - ↑ `parse`
              - ↑ `clock.parse`
              - ↑ `unattended/brief_slots.times_given`
            - `unattended/brief_words.window_refusal` — 보고 창의 고름을 안 건 말 — 그 뒤 대화에서 바꾸셨다(STALE) · 시각의 꼴(BAD · `detail`) · 시각표를 못 읽었다(UNREAD · `detail`).
              - ↑ `in_force`
            - `apply_window` — 창에서 더하고 빼신 것을 지금 걸린 시각표 위에 건다 — 맞춘 시각표(`fit_window`)가 다르면 걸고, 건 뒤 다시 읽어 말한다.
              - `fit_window` — 창에서 더하고 빼신 것을 얹은 시각표 — 창이 보여 드리지 않은 시각은 안 뺀다.
                - `unattended/brief_slots.squeezed` — 기다릴 틈이 `BRIEF_ROOM_MIN` 분보다 짧은 시각 — (시각, 붙은 다음 시각 · 그날 끝이면 None, 틈 분).
                  - ↑ `windows`
                  - ↑ `clock.utc_now`
                  - ↑ `on_day`
              - `unattended/brief_schedule.save` — 시각표를 건다 — 걸려 있던 자리 밖에서 보기(`away`)와 스스로 로그인한 보고의 범위(`signed`)는 그대로 실어 둔다(시각을 바꿔도 켜고 끄기 · 지금 짓는 보고의 한 줄은 안 바뀐다). 스스로 로그인을 켜는 칸은 없다 — 시각이 걸린 것이 곧 그 시각의 로그인이라, 옛 파일의 `login` 칸은 옮기지 않아 다시 걸면 걷힌다.
                - ↑ `read_brief`
                - ↑ `unattended/unattended_store.Unreadable`
                - ↑ `unattended/unattended_store.write_json`
                - ↑ `clock.utc_stamp`
                - ↑ `clock.utc_now`
              - ↑ `unattended/brief_schedule.load`
              - `unattended/brief_words.window_reply` — 보고 창에 돌려 적을 말 — 걸지 않은 시각을 다 까닭과 함께, 더하고 뺀 것을 사실대로 댄다.
                - `gap_words` — 틈이 모자란 까닭의 구절 — 붙은 다른 시각이 있으면 그와 몇 분, 없으면 그날 끝까지 몇 분.
                - `unattended/brief_slots.latest_start` — 보고 시각을 둘 수 있는 가장 늦은 「HH:MM」 — 그날이 끝나기 전에 `BRIEF_ROOM_MIN` 분이 남는 때.
                - ↑ `in_force`
            - ↑ `unattended/unattended_store.Unreadable`
            - `unattended/brief_schedule.put` — 걸린 시각표 파일의 칸 하나만 바꿔 쓴다 — 다른 칸은 그대로 옮겨 적는다.
              - ↑ `read_brief`
              - ↑ `unattended/unattended_store.write_json`
          - `unattended/window_link.ask_window` — 보고 창 손 한 번(사용자 폴더 `folder`) — 표준 출력. 못 돌았으면 빈 글.
            - ↑ `proc_base.run_python`
        - `window_away` — 보고 창에서 고르신 「자리 밖에서 보기」(`picked` — 켬인가 · 고른 때)를 건다(`apply_away`) — 창 곁의 손이 없을 때의 뒷받침이다(그 손은 같은 일을 `clock.py away` 로 바로 한다). 받았나와 까닭을 그 창에 돌려 적는다.
          - ↑ `unattended/away_mail.late`
          - ↑ `clock.parse_chosen`
          - `unattended/away_mail.apply_away` — 「자리 밖에서 보기」를 켜거나 끈다 — 보고 창의 누름(창 곁의 손 · 시계 판)과 대화(`clock.py away`)가 함께 쓰는 한 자리. 걸린 보고를 읽고, 따르나를 가르고(`away_verdict`), 켤 때는 본인 주소를 주소록 손의 「나」에서 받아(못 받으면 안 켠다) 시각표 파일의 칸 하나로 적는다.
            - ↑ `unattended/brief_schedule.load`
            - `away_refusal` — 자리 밖에서 보기를 안 바꾼 말 — 걸린 보고가 없다(UNSET · 못 읽은 까닭 `detail`) · 뒤에 대화에서 바꾸셨다(STALE) · 본인 주소를 못 받았다 (NO_ADDRESS) · 시각표를 못 읽었다(UNREAD) · 그 사이 보고가 내려졌다(GONE).
              - `away_now` — 지금 켜져 있나의 한 구절 — 거절할 때마다 함께 댄다.
            - ↑ `unattended/brief_schedule.away_of`
            - `away_verdict` — 자리 밖에서 보기의 고름을 따르나 — 나중의 말씀이 이긴다: 걸어 둔 고른 때보다 앞이면 STALE(그 사이 대화에서 바꾸셨다), 같으면 AGAIN(이미 받은 그 누름), 아니면 NEW.
              - ↑ `clock.parse`
            - `away_words` — 켜고 끈 뒤의 말 — 켰으면 어느 보고(`next_t` · 오늘 남은 칸이 없으면 내일 첫 시각 `first`)부터 보내나.
            - `unattended/brief_day.next_slot` — 다음 사람 없는 보고의 시각 — 지금 모습(`state` · 모르면 None — 오늘 남은 첫 칸을 댄다)의 그날 장부에서 오늘 아직 안 띄운 칸 가운데 끝나지 않은 첫 것. 없으면 None. `folder` 는 앞 칸이 띄운 보고의 잠금을 볼 자리.
              - `today_of` — 그날 장부의 칸만 읽는다 — 지금 모습을 안 바꾸고, 날이 바뀌었으면 빈 칸들(지난날 줄은 안 셈한다).
                - ↑ `migrated`
                - ↑ `unattended/brief_slots.seoul_date`
              - ↑ `unattended/brief_slots.windows`
              - ↑ `unattended/brief_state.slot_state`
            - `unattended/clock_book.load_or_none` — 보이기만 하는 쪽의 판의 상태 — 그 순간 못 읽었으면 None(그날 장부 없이 서는 말이 쓴다).
              - ↑ `load`
              - ↑ `unattended/unattended_store.Unreadable`
            - ↑ `clock.utc_now`
            - `own_address` — 본인 주소 — 형제 스킬 company-directory 의 「나」(`DIRECTORY_ME`)가 사용자 폴더의 임시 폴더에 낸 사람 파일의 주소 하나. 내는 것 — (주소, "") 나 ("", 까닭).
              - ↑ `proc_base.run_python`
            - ↑ `clock.utc_stamp`
            - ↑ `unattended/brief_schedule.put`
            - ↑ `unattended/unattended_store.Unreadable`
          - ↑ `unattended/window_link.ask_window`
      - `brief_step` — 판의 띄우기 — 지금 칸을 고르고, 그 칸에서 살펴볼 때면 사내 세션의 답을 잡고(`session_now`), 부를 판이면 입구를 한 번 부르고 (`self_login`), 세션이 살았으면 스캔에 한 판을 청해(`scan_door.ask_round`) 그 판의 세션 답으로 띄우거나 기다린다.
        - ↑ `unattended/brief_schedule.load`
        - `slot_now` — 지금 칸 — 그날 장부를 열고(날이 바뀌었으면 새 장부) 지금 든 칸을 고른다.
          - ↑ `unattended/brief_told.today`
          - `unattended/brief_slots.current` — 지금 든 칸 — (차례, 시각, 덮는 첫때, 시작, 끝). 첫 시각 전 · 칸 사이 · 마지막 칸 뒤면 None.
            - ↑ `windows`
          - `unattended/brief_day.slot_of` — 그날 장부의 그 시각 칸 — 없으면 빈 칸을 만들어 넣는다.
        - ↑ `unattended/brief_state.slot_state`
        - `session_now` — 이 칸에서 쓸 사내 세션의 답 — 스캔 판이 그 칸 안 · 마지막 살펴보기와 시계의 앞 판(`since`) 뒤에 손에서 받은 답이 있으면 그것(세션 파일이 새로 쓰여 스캔이 돌았으면 그 판으로 바로 띄운다), 없으면 틈(`spaced`)을 지켜 손에 한 번 묻는다.
          - `unattended/scan_door.answer_since` — `after` 뒤(같은 초는 안 든다)에 시작한 스캔 판이 손에서 받은 사내 세션의 답 — 그런 판이 없거나 답이 없으면 None.
            - `started_since` — `status --json` 의 마지막 판이 `since`(초까지 — 판의 때는 초까지 적힌다) 뒤에 시작했으면 그 판의 칸, 아니면 None.
              - ↑ `clock.parse`
            - `status` — 스캔의 `status --json` 한 장 — 못 부르거나 · 끝 줄이 JSON 사전이 아니거나 · 꼴 번호를 모르면 None. `dry_run` 이면 작업 스케줄러에 안 묻는다.
              - ↑ `proc_base.run_python`
          - `unattended/brief_state.looked_after` — 그 칸의 사내 세션 답이 새것이려면 그 뒤에 섰어야 하는 때 — 칸의 시작 · 그 칸의 마지막 살펴보기 · 시계의 앞 판(`since` · 없으면 안 센다) 가운데 가장 늦은 것. 앞 판 뒤에 선 답만 이 판이 처음 보는 답이다 — 앞 판이 이미 쓴 답을 다시 쓰면 그 사이 살아난 세션을 놓친다.
            - ↑ `clock.parse`
          - `unattended/session_login.look` — 사내 세션이 살았나 — 손의 `session` 한 번의 종료 값. 로그인 화면을 열지 않는다.
            - ↑ `proc_base.run_python`
          - `unattended/brief_state.spaced` — 손에 다시 물어도 되나 — 그 칸의 마지막 살펴보기에서 `BRIEF_TRY_GAP_MIN` 분이 지났다(작업이 더 자주 깨워도 SSO 를 촘촘히 안 두드린다).
            - ↑ `clock.parse`
            - ↑ `unattended/brief_slots.minute`
        - `self_login` — 보고 시각을 건 PC 의 띄우기 앞 — 부를 판이면(`login_due` — 그날 첫 시각의 한 번 · 뒤 시각의 칸에서 세션이 없을 때 한 번) 입구를 사람 없는 꼴로 한 번 부르고 그 끝을 적는다(끊긴 세션 앞의 부름이면 `lost` — 그 로그인으로 띄운 보고의 창이 그것을 말한다). 내는 것 — (그 뒤의 세션 답, 부르기 전의 답, 입구의 끝 — 안 불렀으면 None).
          - `unattended/brief_state.login_due` — 이 판이 스스로 로그인의 입구를 부를 판인가 — LOGIN_DAILY 그날 첫 시각의 한 번(세션이 살았어도 — 입구가 그 윈도 로그온의 평소 Edge 로그인을 먼저 한다) · LOGIN_SLOT 뒤 시각의 칸에서 세션이 없을 때 한 번 · "" 안 부른다.
          - `unattended/session_login.sign_in` — 스스로 로그인 한 번 — 내는 것 — {at, ok: True} 나 {at, ok: False, said}.
            - `call` — 입구 한 번을 사람 없는 꼴로 부른다(사람이 쳐야 하는 자리에서는 입구가 기다리지 않고 끝난다). 내는 것 — ({at, ok, said?}, 종료 값 · 못 불렀으면 None, 표준 출력의 끝 줄). 못 섰으면 `said` 에 입구의 끝말(표준 오류의 끝 줄)이나 까닭을 줄여 싣는다.
              - ↑ `clock.utc_stamp`
              - `login_parts` — 스스로 로그인이 부를 것 — (입구 · 없으면 None, node · 없으면 None).
                - `entrance` — 형제 스킬 ep-login 의 입구 — `LOGIN_ENTRANCE_ENV`, 없으면 손과 같은 스킬 뿌리의 그 스킬. 없으면 None.
              - `command_of` — 입구 · node 로 입구의 명령줄(`args` — 스스로 로그인 · 돌려주기) — 하나라도 없으면 None.
              - ↑ `proc_base.quiet`
          - `session_after` — 입구를 부른 뒤의 세션 답 — 섰으면 살았다.
            - ↑ `unattended/session_login.look`
        - `unattended/scan_door.ask_round` — 스캔에 「지금 한 판」을 청하고(`run_now`) 그 판의 세션 답을 읽는다 — (세션 답 · 판이 돌았는데 답이 없으면 None, "") 이나 판이 안 돌았으면 (None, 까닭 — SCAN_UNREACHED 못 불렀다 · SCAN_LATE 앞 판이 시한 안에 안 끝나 건너뛰었다 · SCAN_STOPPED 판을 못 하고 멈췄다).
          - `run_now` — 스캔에 「지금 한 판」을 청한다 — 세션을 기다리던 주기도 건너뛰고 · 앞 판이 돌면 `SCAN_WAIT_S` 안에서 기다렸다.
            - ↑ `proc_base.run_python`
          - ↑ `status`
          - ↑ `started_since`
        - ↑ `clock.utc_now`
        - `missed_line` — 청한 스캔 판이 안 돈 판 끝의 한 줄 — 왜(`SCAN_MISSED_WORDS`) · 언제까지 다음 판에 다시 청하나.
          - ↑ `unattended/brief_words.end_words`
        - ↑ `clock.utc_stamp`
        - `waiting_line` — 못 띄운 판 끝의 한 줄 — 왜(세션 없음 · 손 오류 · 이 판의 스스로 로그인이 안 섰다 · 섰는데 그 뒤 메일함 읽기가 졌다) · 언제까지 기다리나.
          - ↑ `unattended/brief_words.end_words`
        - `note_launch` — 띄우는 판 — 이 보고가 세션 없이 선 스스로 로그인 위에서 뜨면 그 로그인한 때와 이 보고의 끝을 보고 창이 읽는 자리에 남긴다 (`note_signed` — 그 로그인이 사람의 평소 Edge 에서 메일 · 일정 창을 닫고 EP 포털을 죽였다는 것을 그 보고의 창이 말한다): 그 칸의 로그인이 섰다(뒤 시각 — 칸의 로그인은 끊긴 세션에서만 부른다) · 그날의 한 번이 끊긴 세션에서 섰다(그날 첫 시각의 칸만). 살아 있던 세션 앞의 부름은 로그인을 새로 했는지 몰라 안 남긴다.
          - `unattended/brief_state.slot_login` — 그 칸의 띄우기 앞에 부른 입구의 끝 {at, ok, said, lost} — 첫 시각의 칸은 그날의 한 번(그날 장부의 `login`), 뒤 시각은 그 칸의 `login`. 안 불렀으면 {}.
          - `unattended/brief_schedule.note_signed` — 세션이 없다가 스스로 로그인한 때를 시각표 파일의 `signed` 칸에 남긴다 — {at 로그인한 때, until 그 로그인으로 띄운 보고가 글을 남길 수 있는 끝(띄운 때 `launched` · 안 주면 로그인한 때에서 `BRIEF_LOCK_STALE_S` — 띄운 보고가 그 뒤로는 끝난 것이다)}. 일일 보고의 창이 그 사이에 지은 보고에 한 줄을 세운다.
            - ↑ `put`
            - ↑ `clock.utc_stamp`
          - ↑ `clock.parse`
        - `unattended/claude_launch.launch` — 권한 · 부탁 글을 사용자 폴더에 지어 claude 를 띄우고 기다리지 않는다(출력은 `LAUNCH_LOG_FILE`). 내는 것 — {at, pid, born(뜬 때 · 못 물었으면 None), log} 이나 {at, error}.
          - `plan` — (띄울 명령, `--settings` 로 줄 권한, 표준 입력으로 줄 부탁 글). `at` 은 띄우는 칸의 시각(없으면 첫 시각), `skipped` 는 그 앞에 건너뛴 시각.
            - `places` — 띄운 보고가 쓰는 자리 — 손 · 주소록 손(신원 손도) · 일정 손 · 회의실 손 · 결재 손 · 형제 스킬 mailbox-scan 의 읽는 명령 · 보고 창 · 업무 파일의 쓰는 손 · 스킬 폴더 · 사용자 폴더(`folder`). 없는 주소록 · 일정 · 회의실 · 결재 손은 뺀다.
            - `commands` — 열린 명령 — 권한 규칙의 꼴(끝의 「 *」는 뒤에 인자가 온다). 경로는 「C:/…」 꼴로 따옴표에 싼다 — Git Bash 와 파이썬이 함께 읽는다.
          - ↑ `unattended/unattended_store.write_json`
          - `unattended/launch_base.child_env` — 띄울 claude 의 환경 — 겹친 세션의 표지를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다(`C.RUNNER_HEADER`). 이미 든 다른 머리 줄은 그대로 둔다.
            - `_loopback_proxy` — claude 의 요청이 루프백 프록시를 지나나 — `ANTHROPIC_BASE_URL` 이 `http://<루프백>:<포트>/…` 일 때만.
          - ↑ `detach.detached`
          - ↑ `clock.utc_stamp`
          - `unattended/launch_base.process_born` — 그 번호의 프로세스가 뜬 때(윈도 FILETIME 의 정수) — 번호와 함께 적어 두면 끝난 프로세스의 번호를 남이 받은 것을 가린다.
            - ↑ `_born`
        - `unattended/brief_told.told_lines` — 이 판에 띄우는 보고가 말할 줄 — 마지막 보고 뒤 건너뛴 칸 · 글 없이 끝난 칸 · 못 띄운 칸 · 지난날 줄 · 못 간 메일.
          - ↑ `unattended/brief_words.told_words`
          - ↑ `unattended/brief_state.untold`
        - `launched_line` — 띄운 판 끝의 한 줄 — 띄웠나와 왜 그 판이었나(세션이 있었다 · 스스로 로그인했다 · 입구를 먼저 불렀다) · 출력 자리.
      - `unattended/window_link.window_presses` — 보고 창에서 누르신 「일정에 넣기」를 거둔다 — 창 곁의 손이 없을 때의 뒷받침이다.
        - ↑ `edge_listening`
        - ↑ `ask_window`
      - `unattended/loan.give_back_step` — 시계 판 끝의 돌려주기 — 돌려줄 로그인(그날 장부의 보고 앞 로그인 가운데 그 보고가 끝나고 `GIVE_BACK_AFTER_MIN` 분이 지난 것 · 단추가 빌렸는데 쓰는 일이 더 없는 것)이 있고, 그 세션을 지금 쓰는 일이 없으면(`in_use`) 돌려주는 문을 한 번 부르고 그 끝을 빌림 파일과 그날 장부의 그 로그인 기록(`GIVEN`)에 적는다 — 적힌 로그인은 다시 안 돌려준다(SSO 가 안 서는 로그온의 4 도 그 끝으로 적혀 그날 다시 안 부른다). 잠금을 다른 손이 쥐었거나 빌림 파일을 그 순간 못 읽으면 다음 판에 다시 본다.
        - ↑ `unattended/brief_schedule.load`
        - `locked` — 빌리고 돌려주는 잠금 — `wait_s` 안에 쥐면 그 잠금, 못 쥐면 None(다른 손이 입구를 부르는 중이다).
          - ↑ `oslock.OsLock`
        - `loan_of` — 오늘(서울)의 빌림 파일 {date, given: [돌려준 끝 {at, ok, of, line | said, typed?}], lent: 빌린 로그인 {at, ok, said?} | None, users: [그 세션을 쓰는 일 {why, until}]} — 없거나 날이 지났거나 글이 깨졌으면 빈 오늘의 것. 그 순간 못 읽으면 `st.Unreadable`(빈 것으로 읽어 쓰면 오늘 돌려준 것을 잊고 또 돌려준다).
          - ↑ `unattended/unattended_store.read_json`
          - ↑ `unattended/unattended_store.Unreadable`
          - ↑ `unattended/brief_slots.seoul_date`
        - ↑ `unattended/unattended_store.Unreadable`
        - `loans_of` — 그날 돌려줄 로그인 — 시계가 끊긴 세션 위에서 세운 보고 앞 로그인(첫 시각은 `lost` 인 그날의 한 번 · 뒤 시각은 칸의 한 번 — 뒤 시각은 끊긴 세션에서만 부른다) 가운데 섰고 아직 돌려준 끝이 없는 것. 그 칸이 띄웠든 못 띄웠든 든다 — 로그인은 이미 평소 Edge 의 포털을 죽였다.
          - ↑ `unattended/brief_slots.windows`
          - ↑ `unattended/brief_state.slot_login`
        - ↑ `unattended/brief_slots.seoul_date`
        - `due_at` — 그 로그인을 돌려줄 때 — 그 로그인 뒤에 띄운 보고가 다 끝난 때(`launched_end` — 도는 동안은 기다리고, 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다 · 못 띄운 것은 띄우려던 때)와 로그인한 때 가운데 늦은 것에서 `GIVE_BACK_AFTER_MIN` 분 뒤. 그 칸이 아직 안 띄웠고 칸이 안 끝났으면 None (그 칸이 곧 그 세션으로 띄운다) · 보고가 아직 돌면 None. 뒤 칸이 같은 세션으로 띄운 보고도 그 로그인의 것으로 센다.
          - ↑ `clock.parse`
          - ↑ `unattended/brief_reports.launched_end`
        - `in_use` — 그 세션을 지금 쓰는 프로그램이 있나 — 시계가 띄운 보고가 돈다 · 보고 창의 단추가 맡긴 일이 그 세션을 쓴다(`users_of`).
          - ↑ `unattended/brief_reports.lock_held`
          - `users_of` — 그 세션을 지금 쓰는 일들 {why, until} — 쓸 끝(`until`)이 안 지난 것만. 끝은 쓰겠다고 할 때 그 일의 천장 뒤로 두고(놓는다고 하기 전에 죽은 손이 영영 붙들지 않게), 결재 창처럼 사람이 그 세션에서 누를 일은 놓을 때 `GIVE_BACK_AFTER_MIN` 분 뒤로 고친다.
            - ↑ `clock.parse`
        - ↑ `clock.parse`
        - ↑ `users_of`
        - ↑ `unattended/brief_reports.lock_held`
        - `wake` — 돌려줄 때(`due`)에 시계 판 한 번을 부르는 한 번만의 작업을 걸거나 그 때로 고친다(`clock_task.GIVE_BACK_TASK_NAME` — 돌고 나면 작업 스케줄러가 지운다). 그 판이 돌려주기를 한다 — 놓쳐도 시계의 다음 판이 한다.
          - `unattended/task_base.write_xml` — schtasks /XML 이 받는 꼴로 쓴다 — UTF-16(BOM).
          - `unattended/clock_task.give_back_xml` — 돌려줄 때(`at` · 이 PC 의 시각)에 시계 판 한 번을 부르는 한 번만의 작업 정의 — 부르는 명령은 시계 작업과 같다(`tick_arguments`).
            - `unattended/task_base.once_definition` — 한 번만 도는 작업의 정의(XML) — 그 때(`at` · 이 PC 의 시각)에 한 번 깨고, 그 때를 놓쳤으면 깰 수 있을 때 곧 돈다.
              - `user_id` — 작업을 돌릴 사용자 — 「도메인\이름」(도메인이 없으면 이름).
              - `windowless_python` — 창 없는 파이썬(pythonw.exe) — 지금 도는 파이썬 곁. 없으면 지금 파이썬(창이 뜬다 — 부르는 쪽이 알린다).
            - `tick_arguments` — 작업이 부르는 명령의 인자 — 틀(`TICK_ARGUMENTS`)에 입구 · 사용자 폴더 · 손을 채운다.
          - `unattended/task_base.ask` — 작업 스케줄러(schtasks) · PowerShell 을 한 번 띄워 답을 받는다 — 출력은 물을 때 `decode` 로 푼다.
            - `Answer` — 작업 스케줄러 · PowerShell 한 번의 답 — 종료 값과 받은 그대로의 표준 출력 · 표준 오류. 글자(`out` · `err`)는 읽는 쪽이 물을 때만 푼다 — 종료 값만 보는 쪽이 못 푸는 출력에 넘어지지 않게.
              - `Answer.out` — 표준 출력을 푼 글자.
                - `decode` — 작업 스케줄러 · PowerShell 의 출력 — UTF-16(BOM · 0 바이트)이나 UTF-8, 아니면 콘솔의 OEM 코드 페이지(한글 윈도는 949)다.
              - `Answer.err` — 표준 오류를 푼 글자.
                - ↑ `decode`
          - `unattended/task_base.register_command` — 정의 파일로 작업을 거는 schtasks 명령줄.
        - `retry_wait` — 앞 판에 진 돌려주기 뒤 `BRIEF_TRY_GAP_MIN` 분이 안 지났나.
          - ↑ `clock.parse`
          - `failures` — 오늘 돌려주는 문이 맺지 못하고 진 끝들 — 섰다 · SSO 가 안 선다가 아닌 것(시한 · Edge 를 못 찾음 따위).
        - `hand_back` — 돌려주는 문을 한 번 부르고 그 끝을 빌림 파일에 적는다.
          - `unattended/session_login.give_back` — 사람의 로그인을 돌려준다 — 같은 입구의 돌려주는 문(`GIVE_BACK_ARGS`) 한 번: 평소 Edge 에 로그인을 다시 열고 쓸모가 끝난 EP 탭을 닫는다.
            - ↑ `call`
          - `settled` — 그 끝으로 그 로그인을 맺나 — 섰다 · SSO 가 안 선다(그날 다시 안 부른다) · 진 것이 오늘 `GIVE_BACK_TRIES` 번에 닿았다(판마다 평소 Edge 에 로그인을 거듭 열지 않는다). 그 밖에 진 것은 맺지 않고 `BRIEF_TRY_GAP_MIN` 분 뒤 판에 다시 부른다.
            - ↑ `failures`
          - `save` — 빌림 파일을 바꿔 끼워 쓴다 — 못 쓰면 OSError.
            - ↑ `unattended/unattended_store.write_json`
        - ↑ `settled`
        - `given_words` — 돌려준 끝 한 구절 — 판 끝의 줄과 status 가 쓴다.
          - ↑ `clock.seoul`
          - ↑ `clock.parse`
  - `unattended/scan_door.home_of` — 사용자 폴더 — 준 것(`--dir`)이 있으면 그것, 없으면 스캔이 대는 자리(사본을 안 든다). 못 정하면 None.
    - ↑ `status`
  - `unattended/clock_setup.cmd_register` — 시계를 작업 스케줄러에 건다 — 손을 정하고, 보고 시각표 요청을 재고, 정의를 지어(보이기만 · 받나만 묻기도) 건 뒤 `--at` 이 있으면 시각표를 건다.
    - ↑ `unattended/scan_door.mail_hand`
    - `brief_wanted` — `--at` · `--claude` 를 재어 (보고 시각표, claude, 거절의 말). 보고를 안 청했으면 (None, None, ""). 시각을 안 주면 기본 시각 하나다.
      - ↑ `unattended/brief_slots.times_given`
      - ↑ `unattended/brief_words.in_force`
      - ↑ `unattended/brief_schedule.load`
      - `held_setting` — 지금 걸린 보고 시각표 — 글이 깨진 파일은 없는 것으로 본다(새로 걸면 고쳐진다). 그 순간 못 읽었으면 거절의 말을 낸다 — 빈 것으로 읽으면 claude · 자리 밖에서 보기를 기본값으로 덮어 쓴다.
        - ↑ `unattended/brief_schedule.read_brief`
        - ↑ `unattended/unattended_store.Unreadable`
        - ↑ `unattended/brief_schedule.setting_of`
      - `unattended/brief_words.room_words` — 틈이 모자란 시각(`brief_slots.first_tight`)의 거절의 말 — 그 시각에는 시계 판이 안 돌아 보고가 날마다 안 뜬다.
        - ↑ `gap_words`
        - ↑ `unattended/brief_slots.latest_start`
      - `unattended/brief_slots.first_tight` — 기다릴 틈이 모자란 첫 시각 — (짚을 시각, 붙은 다른 시각 · 그날 끝이면 None, 틈 분). 붙은 두 시각 가운데 새로 더하신 쪽(`added`)을 짚는다.
        - ↑ `squeezed`
      - `unattended/launch_base.pick_claude` — 띄울 claude 를 고른다 — 준 것(`--claude`)이 있으면 그것, 없으면 걸어 둔 것(그 파일이 있으면 적힌 그대로 — 바로 가기를 풀어 판의 자리를 굳히지 않는다), 그것도 없으면 PATH. 못 찾으면 None.
        - `find_claude` — 띄울 claude 의 자리 — `--claude` 가 가리키는 파일, 없으면 PATH 에서 `CLAUDE_NAMES` 차례. 못 찾으면 None.
    - `unattended/clock_task.task_xml` — 등록할 작업 정의(XML) — 바탕의 틀(`task_base.definition`)에 주기 · 사용자 폴더 · 손 · 켜짐을 채운다.
      - `unattended/task_base.definition` — 등록할 작업 정의(XML) — 틀(`DEFINITION`)에 설명 · 주기(분) · 첫 판의 때 · 로그온 뒤 첫 판(분) · 한 판의 시한(분) · 창 없는 파이썬이 받을 인자 · 작업 폴더 · 켜짐을 채운다.
        - ↑ `user_id`
        - ↑ `windowless_python`
      - ↑ `tick_arguments`
    - ↑ `unattended/task_base.windowless_python`
    - `unattended/task_base.shown` — 사람에게 보일 명령줄 — 빈칸이 든 인자는 따옴표에 싼다.
    - ↑ `unattended/task_base.register_command`
    - `show_brief_plan` — 걸면 띄울 것 — 명령 · 보고 시각의 로그인 명령 · 열린 명령 · 막은 명령(`--dry-run`).
      - ↑ `unattended/claude_launch.plan`
      - `unattended/brief_words.window_words` — 언제 띄우나의 한 구절 — 그날의 칸(`brief_slots.windows`)을 받는다.
        - ↑ `end_words`
      - ↑ `unattended/brief_slots.windows`
      - ↑ `clock.utc_now`
      - ↑ `unattended/task_base.shown`
      - `unattended/session_login.login_command` — 스스로 로그인이 부를 명령 — 입구나 node 가 없으면 None(거는 줄 · `--dry-run` 이 그 PC 에서는 로그인이 안 선다고 말한다).
        - ↑ `command_of`
        - ↑ `login_parts`
    - ↑ `unattended/task_base.write_xml`
    - `validate_task` — 작업 스케줄러가 지은 정의를 받나만 묻는다(등록 안 함) — 받으면 0, 거절하면 그 말과 1.
      - ↑ `unattended/task_base.ask`
      - `unattended/task_base.validate_command` — 작업 스케줄러가 정의를 받나만 묻는 PowerShell 명령줄(등록 안 함) — 정의 파일의 자리는 환경변수 `env` 로 받는다.
      - `unattended/task_base.validate_env` — 정의를 받나 묻는 PowerShell 의 환경 — 지금 환경에 정의 파일의 자리를 `env` 라는 이름으로 얹는다.
      - `unattended/task_base.accepted` — 정의를 받나 물은 답(`validate_command`)이 「받는다」인가 — 종료 0 이고 끝 글이 `VALIDATE_OK` 다.
    - `put_task` — 정의 파일로 작업을 건다 — 작업 스케줄러가 거절하면 그 말을 내고 False.
      - ↑ `unattended/task_base.ask`
      - ↑ `unattended/task_base.register_command`
    - `save_and_tell` — 보고 시각표를 걸고 그 한 줄을 낸다 — 보고 시각의 로그인과 그 값을 늘 말하고, 이 PC 에서 로그인 입구를 못 찾으면 그것도 말한다.
      - ↑ `unattended/brief_schedule.save`
      - ↑ `unattended/unattended_store.Unreadable`
      - `set_line` — 보고 시각표를 건 뒤의 한 줄 — 언제 띄우나 · 보고 시각의 로그인과 그 값 · 띄울 claude.
        - ↑ `unattended/brief_words.window_words`
        - ↑ `unattended/brief_slots.windows`
        - ↑ `clock.utc_now`
      - `unattended/window_link.tell_window` — 대화에서 시각표를 바꾼 뒤 열린 보고 창에 바로 알린다 — 이 PC 의 디버깅 포트가 받을 때만 창의 지금 모습을 적는다(`state.sync`). 내는 것 — 알렸으면 대화 줄 끝에 붙일 구절(「 · 열린 보고 창에 …」), 창이 없거나 못 닿으면 ""(창은 그 뒤 시계 판이나 다음 거두기가 알린다).
        - ↑ `edge_listening`
        - ↑ `state.sync`
      - ↑ `unattended/session_login.login_command`
  - `unattended/clock_setup.cmd_at` — 보고 시각표를 걸고 바꾼다(`at`) — 걸었는데 시계가 작업 스케줄러에 안 걸려 있으면 그렇다고 알린다.
    - `put_times` — 보고 시각표를 걸고 바꾼다 — 재고(`brief_wanted`), 보이기만 하거나 건다.
      - ↑ `brief_wanted`
      - ↑ `show_brief_plan`
      - ↑ `save_and_tell`
    - ↑ `unattended/scan_door.mail_hand`
    - ↑ `unattended/task_base.ask`
    - `unattended/task_base.query_command` — 걸린 작업의 정의를 묻는 schtasks 명령줄.
  - `unattended/clock_setup.cmd_off` — 보고 예약을 내린다(`off`) — 내렸으면 열린 보고 창에 알린다.
    - ↑ `unattended/window_link.tell_window`
    - `unattended/brief_schedule.clear` — 보고를 내린다 — 걸려 있었으면 True.
  - `unattended/clock_setup.cmd_away` — 자리 밖에서 보기를 켜고 끈다 — 대화의 말(고른 때는 지금)과 창 곁의 손이 준 보고 창의 누름(`--chosen-at`)이 같은 길로 간다.
    - ↑ `clock.parse_chosen`
    - ↑ `clock.utc_now`
    - ↑ `unattended/away_mail.apply_away`
    - ↑ `unattended/scan_door.mail_hand`
    - ↑ `unattended/brief_schedule.away_of`
    - ↑ `unattended/brief_schedule.load`
    - ↑ `unattended/window_link.tell_window`
  - `unattended/clock_setup.cmd_window_times` — 보고 창에서 고르신 보고 시각을 건다 — 창 곁의 손이 준 고름(시각들 · `--window-base` · `--chosen-at`)을 시계 판이 창에서 받을 때와 같은 자(`brief_window.take_window_times`)로 잰다.
    - ↑ `unattended/brief_schedule.load`
    - ↑ `unattended/brief_words.in_force`
    - ↑ `unattended/brief_window.take_window_times`
  - `unattended/clock_setup.cmd_status` — 시계 작업 · 보고 예약을 보인다 — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 시계 작업 줄, 시계가 없고 옛 시각표만 있으면 옮겨 받으라는 줄, 그 뒤 보고 예약 줄(`brief_status.describe`)을 찍는다.
    - ↑ `unattended/task_base.ask`
    - ↑ `unattended/task_base.query_command`
    - `task_lines` — 시계 작업의 줄 — 안 물었으면(`done` 이 None) 물을 명령, 없거나 못 읽었으면 그 답, 걸렸으면 정의(`d`)의 간격 · 켜짐 · 부르는 것.
      - ↑ `unattended/task_base.shown`
      - ↑ `unattended/task_base.query_command`
    - `unattended/task_base.read_definition` — 작업 스케줄러가 돌려준 정의(XML)에서 사람에게 말할 것 — 간격 · 켜짐 · 한 번에 하나 · 부르는 인자.
    - `legacy_only` — 옛 보고 시각표는 있는데 새 시각표가 없나 — 옮겨 받기를 아직 안 한 PC.
    - `unattended/brief_status.describe` — status 가 말할 줄을 엮는다 — 걸었나 · 머리 줄 · 그날 장부 줄 · 시각마다 오늘 어떻게 됐나. `task` 가 False 면 시계 작업이 안 걸렸다 (None 은 안 물었다).
      - ↑ `unattended/brief_schedule.load`
      - `unattended/brief_words.unset_lines` — 보고 예약이 안 걸렸을 때 status 의 줄 — 시각표를 못 읽은 까닭(`problem`)이 있으면 그것과 다시 거는 길.
      - `unattended/brief_words.head_lines` — status 의 보고 예약 머리 줄 — 언제 · 로그인 · claude, 자리 밖에서 보기, 그리고 작업이 안 걸렸다(`task` False) · claude 가 없다 · 틈이 모자라다(`tight` — 거절의 말)의 경고.
        - ↑ `window_words`
        - ↑ `clock.seoul`
        - ↑ `clock.parse`
      - ↑ `unattended/brief_schedule.away_of`
      - ↑ `unattended/brief_slots.windows`
      - ↑ `clock.utc_now`
      - `unattended/brief_schedule.claude_present` — 걸어 둔 claude 가 그 자리에 있나.
      - ↑ `unattended/brief_words.room_words`
      - ↑ `unattended/brief_slots.first_tight`
      - ↑ `unattended/brief_told.today`
      - ↑ `clock.seoul`
      - `unattended/brief_words.day_lines` — status 의 그날 장부 줄 — 지난날 건너뛴 칸의 줄(`before`) · 오늘 스스로 로그인의 입구를 부른 끝마다 한 줄(`logins` — `brief_state.day_logins` · 뒤 시각의 칸에서 부른 것은 그 시각을 단다).
        - ↑ `hhmm`
      - `unattended/brief_state.day_logins` — 그날 스스로 로그인의 입구를 부른 끝들 — (칸의 시각 · 그날 첫 시각의 한 번이면 "", 끝 {at, ok, said})을 부른 차례로.
      - `unattended/loan.status_lines` — status 가 말할 오늘의 돌려주기 — 돌려준 끝마다 한 줄 · 아직 안 돌려준 보고 앞 로그인(언제 돌려주나) · 보고 창의 단추가 빌려 쓰는 중인 로그인. 보이기만 한다 — 그날 장부 · 빌림 파일을 안 고친다.
        - ↑ `loan_of`
        - ↑ `unattended/unattended_store.Unreadable`
        - ↑ `given_words`
        - ↑ `unattended/brief_slots.seoul_date`
        - ↑ `loans_of`
        - ↑ `due_at`
        - ↑ `clock.seoul`
        - ↑ `clock.parse`
      - ↑ `unattended/brief_state.slot_state`
      - `unattended/brief_words.slot_line` — status 의 한 시각 — 칸의 상태(`state` — `brief_state.status_state`) · 건너뛴 까닭(`cause`) · 그 칸의 띄우기 앞에 부른 입구의 끝(`login` — `brief_state.slot_login`)을 말로: 섰다 · 띄웠다 · 짓는 중 · 아직 · 기다린다 · 건너뛰었다와 다음 걸음. 셈은 안 한다.
        - ↑ `end_words`
        - ↑ `hhmm`
        - `looked` — 그 칸에서 살펴본 것의 한 구절 — 처음 · 마지막 때와 수, 답마다의 수(손 오류를 「세션 없음」에 섞지 않는다).
          - ↑ `hhmm`
      - `unattended/brief_state.status_state` — status 가 말할 칸의 상태 — 시계 작업이 안 걸렸고(`task` 가 False) 아직 일이 안 난 칸이 안 끝났으면 UNSCHEDULED, 아니면 칸의 상태.
      - ↑ `unattended/brief_state.skip_cause`
      - ↑ `unattended/brief_state.slot_login`
      - `unattended/brief_words.slot_status_line` — status 의 한 시각의 줄 — 칸의 말(`line`)에 메일 기록의 구절(`mail` — (상태, 기록))을 붙인다.
        - ↑ `mail_words`
      - `unattended/brief_state.slot_mail` — 칸의 메일 기록과 그 상태 — 기록이 없으면 None.
        - ↑ `mail_status`
    - ↑ `unattended/clock_book.load_or_none`
    - ↑ `clock.utc_now`
  - `unattended/clock_setup.cmd_unregister` — 시계 작업을 지우고 보고 예약을 내린다 — 쌓인 파일은 안 건드린다.
    - ↑ `unattended/task_base.shown`
    - `unattended/task_base.delete_command` — 작업을 지우는 schtasks 명령줄.
    - ↑ `unattended/brief_schedule.clear`
    - ↑ `unattended/task_base.ask`
  - `unattended/clock_setup.cmd_adopt` — 시계를 이 홈으로 옮겨 받는다(설치가 업데이트 때 한 홈에서 · 대화가 부른다) — 옛 파일을 옮겨 받고(`take_over`) 걸린 시계만 본다: 이 홈의 입구 · 회사 메일 손을 부르면 그대로, 손으로 고친 꼴이면 안 건드리고, 다른 홈의 입구나 다른 손을 부르면 켜짐을 지켜 시계의 주기(`CLOCK_EVERY_MIN`)로 다시 건다 — 걸린 주기는 옛 스캔의 `--every` 를 베낀 값일 수 있고, 보고 뒤의 돌려주기 · 칸의 틈 규칙이 시계의 주기에 기댄다.
    - ↑ `unattended/take_over.take_over`
    - `held_clock` — 걸린 시계 — 안 걸렸으면 None, 걸렸으면 켜짐 · 주기(분 · 못 읽으면 None)와 인자를 거는 꼴의 칸(`parts` — 손으로 고친 꼴이면 None)으로.
      - ↑ `unattended/task_base.ask`
      - ↑ `unattended/task_base.query_command`
      - ↑ `unattended/task_base.read_definition`
      - `unattended/task_base.is_enabled` — 걸린 정의(`read_definition`)가 켜진 작업인가 — 작업 스케줄러가 「꺼짐」으로 적은 것만 거짓(칸이 없으면 켜짐이 기본이다).
      - `unattended/task_base.interval_minutes` — 작업 정의의 간격(ISO 8601 기간)을 분으로 — 기간의 꼴이 아니거나 분으로 안 떨어지면 None.
      - `unattended/clock_task.arguments_parts` — 걸린 시계의 인자를 틀의 칸(입구 `clock_py` · 사용자 폴더 `home` · 손 `hand`)으로 되읽는다 — 그 틀로 지은 글이 아니면 None.
    - `clock_skip` — 걸린 시계를 건드리지 않을 까닭 — "foreign" 손으로 고친 꼴이다 · "present" 이미 이 홈의 입구와 손을 부른다 · "" 건다(없거나 다른 홈이다).
      - `unattended/task_base.same_path` — 두 경로가 같은 자리인가 — 윈도의 대소문자 · 사이 글자(`/` · `\`) · `..` 를 고른 뒤 견준다.
    - ↑ `unattended/scan_door.mail_hand`
    - ↑ `unattended/task_base.write_xml`
    - ↑ `unattended/clock_task.task_xml`
    - ↑ `put_task`
    - `adopted_line` — 건 뒤의 끝 줄 — 다른 홈의 시계를 다시 걸었으면 그 말(끈 채면 그것도), 새로 걸었으면 옛 시각표를 이번에 옮겨 받았나.
  - `unattended/loan.cmd_lend` — `clock.py lend --why W --ceiling S [--lost]` — 보고 창 곁의 손이 단추의 일을 하기 전(산 세션으로 보고 — 손에 안 묻는다)과 그 일이 세션 없음을 낸 뒤(`--lost`) 부른다.
    - ↑ `unattended/scan_door.mail_hand`
    - `lend` — 보고 창의 단추가 맡긴 일(`why` — put · appr · run)이 사내 세션을 쓴다고 적는다 — 쓰는 동안 시계 판이 돌려주지 않게(쓸 끝은 `ceiling_s` 뒤 — 놓는다고 하기 전에 죽은 손이 영영 붙들지 않게 · `owner` 는 놓을 때 제 것을 찾는 프로세스 번호 — 없으면 이 프로세스). 세션이 끊겨 있으면(`lost` — 모르면 손에 한 번 묻는다) 오늘 이 PC 가 로그인을 돌려준 뒤일 때만 잠깐 다시 로그인한다(빌린 로그인 `lent`). 안 빌리는 때 — 오늘 돌려준 적이 없다(사람이 다른 자리에서 로그인해 끊겼다 · 대화가 세운 세션이 끊겼다 — 전처럼 대화의 EP 로그인을 청한다) · SSO 가 안 서는 로그온 · 그 일이 오늘 빌린 로그인 위에서도 세션 없음을 냈다(`futile` — 판마다 로그인하고 돌려주기를 되풀이하지 않는다) · 빌린 로그인이 섰는데 또 끊겼다(사람이 다른 자리에서 로그인했다 — 판마다 그 창을 다시 닫지 않는다) · 앞 빌림의 로그인이 `BRIEF_TRY_GAP_MIN` 분 안에 못 섰다.
      - ↑ `locked`
      - ↑ `loan_of`
      - ↑ `unattended/session_login.look`
      - ↑ `clock.parse`
      - `given_ok` — 오늘 돌려주는 문이 한 번이라도 섰나 — 그 뒤에 끊긴 세션은 우리가 돌려줘서 끊긴 것이다.
      - `typed_today` — 오늘 돌려주는 문이 SSO 가 안 서는 로그온이라고 했나 — 그러면 그날은 다시 안 부른다(칠 사람이 없고, 아무것도 안 열었다).
      - ↑ `unattended/session_login.sign_in`
      - ↑ `save`
      - ↑ `users_of`
      - ↑ `clock.utc_stamp`
    - ↑ `clock.utc_now`
  - `unattended/loan.cmd_release` — `clock.py release --why W [--hold] [--futile]` — 단추의 일이 끝난 뒤 부른다.
    - ↑ `unattended/scan_door.mail_hand`
    - `release` — 그 세션을 쓴 일 하나(`why` 의 첫 것)가 세션을 놓는다 — 걷고, `hold` 면(결재 창 — 사람이 그 세션이 사는 창에서 누른다) 그 뒤 `GIVE_BACK_AFTER_MIN` 분 더 쓰는 것으로 적는다(빌리지 않은 일도). `futile` 이면(빌린 로그인 위에서도 세션 없음이었다) 그 일에는 오늘 다시 안 빌려 준다.
      - ↑ `locked`
      - ↑ `loan_of`
      - ↑ `users_of`
      - ↑ `clock.utc_stamp`
      - ↑ `save`
      - ↑ `in_use`
      - ↑ `given_words`
      - ↑ `hand_back`
    - ↑ `clock.utc_now`
- `main` — 명령 입구 — 사용자 폴더를 정하고(`--dir` · 없으면 스캔에 묻는다) 받은 명령을 그 손에 나눈다.
  - `parser` — 명령줄의 꼴 — 하위 명령(start · show · watch · list) · 인자 · 도움말.
  - ↑ `unattended/scan_door.home_of`
  - `emit` — JSON 한 줄을 표준 출력에 낸다.
  - `watch` — 지킴이 한 판 — 작업 묶음에 저를 넣고, 사내 세션을 보고, claude 를 띄워 출력을 받아 적고, 끝의 까닭을 적는다.
    - `read_run` — 그 판의 기록 — 없거나 글이 깨졌거나 꼴이 아니면 None(기다려도 안 바뀐다 — 걷기는 폴더의 때로 잰다), 있는데 못 읽으면 `st.Unreadable`.
      - ↑ `unattended/unattended_store.read_json`
      - `run_dir` — 그 판의 폴더 — 새 자리에 없고 옛 자리에 있으면 옛 자리, 아니면 새 자리.
        - `run_roots` — 판 폴더가 서는 자리 둘 — (새 판이 서는 자리, 옛 자리). 도는 판의 폴더는 지킴이가 흐름 파일을 쥐어 못 옮겨, 옛 자리의 판도 읽는다.
      - ↑ `unattended/unattended_store.Unreadable`
    - `Job` — 윈도의 작업 묶음 하나 — 지킴이가 저를 넣고 claude 를 띄우면 claude 와 그 아래가 함께 든다.
      - `Job._limit` — 묶음의 한도 깃발을 `flags` 로 바꿔 건다 — 걸었으면 True.
      - `Job.disarm` — 「마지막 손잡이가 닫히면 묶음 안을 끝낸다」 깃발을 걷는다 — 걷었으면 `armed` 가 거짓이 된다.
        - ↑ `Job._limit`
    - `update_run` — 기록을 다시 읽고 `change` 를 얹어 새 파일로 바꿔 끼운다 — 쓰는 것은 start 와 그 판의 지킴이뿐이라(읽는 쪽은 안 쓴다) 잠금이 없다.
      - ↑ `read_run`
      - ↑ `unattended/unattended_store.write_json`
      - ↑ `run_dir`
    - ↑ `unattended/session_login.look`
    - ↑ `unattended/loan.lend`
    - ↑ `clock.utc_now`
    - `stamp` — 기록의 때 — UTC ISO 8601 을 천분의 일 초까지. 한 판의 때는 다 이 꼴이라 글자끼리 견줘도 시간순이다(일의 끝과 다음 부름은 1 초 안에 붙기도 한다).
      - ↑ `clock.utc_now`
    - ↑ `run_dir`
    - `read_tasks_of` — 그 판의 맡긴 일(start 가 한 번 쓴다) — 없으면 빈 목록, 있는데 못 읽으면 `st.Unreadable`(빈 목록으로 읽으면 일 없는 실행을 띄우거나 다 했다로 맺는다).
      - ↑ `unattended/unattended_store.read_json`
    - `prompt_of` — 실행이 받는 글 — 틀(`PROMPT_TEXT`)의 자리 넷을 채운다.
      - ↑ `clock.seoul`
      - ↑ `clock.utc_now`
    - `child_env` — 띄울 claude 의 환경 — 보고의 실행과 같은 손질(`launch_base.child_env`)에 물려받았을 표지(`CARRIED_MARKS`)를 더 걷고, 띄운 쪽의 이름(`ENTRYPOINT`)을 준다 — 그래야 「대화로 이어 가기」 가 그 세션을 연다.
      - ↑ `unattended/launch_base.child_env`
    - ↑ `proc_base.quiet`
    - `pump` — claude 의 출력을 줄마다 받은 때와 함께 덧붙인다 — 한 줄씩 디스크로 내려, 읽는 쪽이 도는 동안 그 줄까지 본다.
      - ↑ `stamp`
    - `kill_tree` — 그 claude 와 그것이 띄운 셸 · 손을 함께 끝낸다 — 쥔 프로세스의 번호로만.
      - ↑ `proc_base.quiet`
    - `parse_stream` — 흐름 파일 → {session, model, result(마지막 맺음 사건), cost · turns(맺음마다 더한 것), marks: {번호: {state, t, text}}, tools: [부른 때 …], called_since_mark: 마지막 표지 뒤에 부름이 있었나(흐름의 차례로 — 때는 같은 천분의 일 초에 겹칠 수 있다), loose: 마지막 부름 뒤 표지에 안 딸린 글, first · last: 첫 줄 · 끝 줄의 때}. `tasks` 는 맡긴 일의 수 — 그 밖의 번호를 단 표지는 안 센다.
      - `unattended/unattended_store.read_jsonl` — 덧붙인 줄 전부(옛것부터)와 못 읽은 줄의 수 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다.
        - ↑ `store.read_bytes`
        - ↑ `store.Unreadable`
        - ↑ `Unreadable`
      - `split_marks` — 글 한 덩이 → (첫 표지 앞의 글, [(일 번호, 상태, 표지 뒤의 글) …]). 맺는 글의 머리는 번호 0 · 상태 빈 글이다.
    - `untouched` — 끝난 실행에서 아직 손대지 않은 일의 번호 — 표지가 없고, 마지막 표지 뒤로 부름이 하나도 없을 때만(하다 만 일이 있으면 빈 목록 — 이으면 두 번 들 수 있다). 표지를 하나도 안 단 판도 무엇이라도 불렀으면 빈 목록이다.
    - `settle` — 끝난 claude → 기록에 얹을 끝. 맺음 사건이 성공이고 종료 0 이면 다 했다, 아니면 죽었다(끊었으면 끊겼다). 못 끝낸 일이 있으면 사내 세션을 한 번 보고, 없으면 로그인이 끊긴 끝이다 — 손이 종료 3 을 낸 뒤의 일들은 그래서 못 했다.
      - ↑ `run_dir`
      - ↑ `read_tasks_of`
      - ↑ `parse_stream`
      - ↑ `unattended/session_login.look`
      - `tail` — 죽은 판이 남긴 말 — claude 의 오류 출력, 없으면 맺음 글의 끝.
        - ↑ `parse_stream`
      - ↑ `stamp`
    - ↑ `unattended/loan.release`
  - `alive_runs` — 사용자 폴더의 판 가운데 아직 도는 것의 기록 — 새 판부터, 그 순간 못 읽은 판은 뺀다.
    - ↑ `run_roots`
    - `record` — 그 판의 지금 기록 — 아무것도 안 쓴다.
      - ↑ `read_run`
      - ↑ `run_dir`
      - ↑ `read_tasks_of`
      - ↑ `unattended/unattended_store.Unreadable`
      - ↑ `parse_stream`
      - `watcher_alive` — 지킴이가 아직 도나 — 번호를 적기 전이면 맡긴 지 `START_GRACE_S` 안일 때만, 적었으면 그 프로세스가 살았나로. 맡긴 지 `STALE_S` 가 지났으면 번호를 남이 받았어도 죽은 것이다.
        - ↑ `clock.parse`
        - ↑ `clock.utc_now`
        - ↑ `unattended/launch_base.process_alive`
      - ↑ `tail`
      - `task_states` — 일마다 {id, kind, state, at, text, result}. `result` 는 결과 글이 꼴대로면 그 칸들(`result_of`), 아니면 None. 표지가 선 일은 그 낱말 · 그 때 · 그 글이다.
        - `result_of` — 결과 글 → 꼴대로 쓴 결과({said, facts, items, more} — 빈 칸은 뺀다), 꼴이 아니면 None. 꼴 — JSON 객체 하나(코드 블록 하나로 감싸도 된다) · 칸은 `RESULT_KEYS` 안 · said · more 는 글, facts 는 [이름표, 값] 글 짝의 목록, items 는 {label(빈 글 아님), unid, note} 의 목록 · said · facts · items 가운데 하나는 비지 않는다.
          - `text_of` — 빈칸만이 아닌 글이면 그 글, 아니면 None.
    - ↑ `unattended/unattended_store.Unreadable`
  - ↑ `record`
  - ↑ `unattended/unattended_store.Unreadable`
  - `start` — 맡긴 일 하나를 받는다 — 기록을 쓰고 지킴이를 떼어 띄운 뒤 지금 기록을 낸다.
    - `read_tasks` — 맡긴 일 파일 → {brief, tasks: [{id, kind, line, card: {title, lines}}]}. 꼴이 아니면 `Refused(EXIT_ARGS)` — 무엇이 틀렸나를 댄다.
      - `Refused` — 맡길 수 없다 — `code` 는 종료 값, `body` 는 낼 JSON.
      - ↑ `text_of`
    - `work_folder` — 작업 폴더 — `--work`, 없으면 `PAISETUP_WORK`(사용자 환경값을 먼저 — 손을 띄운 쪽이 값을 심기 전에 떴으면 제 환경의 값이 낡았다 — 그다음 이 프로세스의 환경). 없거나 폴더가 아니면 `Refused(EXIT_CANNOT)`.
      - `user_env` — 사용자 환경값(HKCU\Environment) 하나 — 윈도가 아니거나 없으면 "".
      - ↑ `Refused`
    - ↑ `unattended/brief_schedule.load`
    - ↑ `unattended/launch_base.pick_claude`
    - ↑ `Refused`
    - ↑ `unattended/scan_door.mail_hand`
    - `prune` — 끝난 지 `KEEP_DAYS` 가 지난 판을 걷는다 — 기록 폴더와 그 판이 작업 폴더에 쓴 파일 자리. 도는 판은 안 건드린다.
      - ↑ `clock.utc_now`
      - ↑ `run_roots`
      - ↑ `record`
      - ↑ `unattended/unattended_store.Unreadable`
      - ↑ `clock.parse`
    - `new_id` — 새 판의 번호 — 서울 시각(초까지)과 무작위 16 진 여섯 글자.
      - ↑ `clock.seoul`
      - ↑ `clock.utc_now`
    - ↑ `run_dir`
    - ↑ `unattended/unattended_store.write_json`
    - ↑ `stamp`
    - ↑ `proc_base.python_argv`
    - ↑ `detach.detached_tries`
    - ↑ `update_run`
    - ↑ `record`
  - ↑ `Refused`

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `asks.work_value` — 작업 폴더 값 — 사용자 환경값(윈도 레지스트리 `HKCU\Environment`)을 먼저, 그다음 이 프로세스의 값. 설치기가 값을 심기 전에 뜬 프로세스(창 곁의 손 · 그 손을 띄운 대화)는 옛 환경을 들고 있어 사용자 환경값이 진본이다.
- `asks.work_folder` — (작업 폴더, 받은 값) — 값이 없거나 그 폴더가 없으면 폴더 자리가 None.
  - ↑ `work_value`
- `asks.prefill` — 입력 칸에 채울 글 — 친 말, 빈 줄, 어느 보고 창에서 보낸 부탁인가, 그 보고 글의 자리. 친 말은 고치지 않는다.
- `asks.link` — 여는 주소 — 글을 두 번 퍼센트 인코딩한다(VS Code 가 한 번 · 확장이 한 번 푼다). `session` 을 주면 그 대화를 이어 연다(뒤에서 돈 실행의 세션 — 확장의 세션 목록에 드는 것만 이어진다: 작업 폴더에서 돌았고, 띄운 쪽 이름이 프로그램의 것(`sdk-*`)이 아니다.
- `asks._user32` — 창을 묻고 앞으로 올리는 user32 의 Win32 함수를 인자 · 반환 꼴을 매겨 싣는다.
- `asks._image` — 프로세스 번호 `pid` 의 실행 파일 경로 — 못 물으면 빈 글.
- `asks.top_window` — VS Code 창들 가운데 z 차례 맨 위 — (핸들, 제목). 그 실행 파일이 띄운, 보이고 제목이 있는 맨 위 창(주인 없는 창)만 센다.
  - ↑ `_user32`
  - ↑ `_image`
- `asks.names_folder` — 제목이 그 폴더를 대나 — VS Code 설정 `window.title` 의 기본 꼴(「편집기 - 폴더 - Visual Studio Code」 · 「폴더 - Visual Studio Code」).
- `asks.shed_marks` — 손의 환경에서 물려받은 표지(`CARRIED_MARKS`)를 걷는다 — 손이 띄우는 VS Code 와 손이 여는 주소(ShellExecute 가 손의 환경을 넘긴다)가 다 이 환경을 받는다.
- `asks.raise_folder` — `Code.exe <작업 폴더>` — 그 폴더 창이 있으면 VS Code 창들 맨 위로 올리고, 없으면 새 창으로 연다.
- `asks.wait_top` — 맨 위 VS Code 창이 그 폴더를 댈 때까지 — 그 창의 핸들. 천장까지 안 서면 None. 기다리는 동안 `tick` 을 거듭 부른다(손이 살아 있다는 숨 표 — 꺼져 있던 VS Code 가 뜨는 동안 창이 손을 없다고 읽지 않게).
  - ↑ `top_window`
  - ↑ `names_folder`
- `asks.bring_forward` — 그 창을 앞에 세워 본다 — 섰으면 True. Windows 는 사람이 다른 창을 쓰는 동안 뒤의 프로세스가 앞 창을 바꾸는 것을 막는다.
  - ↑ `_user32`
- `asks.brief_of` — 누른 창(`page` — 그 창의 파일 이름)의 보고 이름과 보고 글의 자리 — 그 글이 없으면(`store.page_brief`) ("", None).
  - ↑ `store.page_brief`
  - ↑ `brief_inline.plain`
  - ↑ `brief_text.parse`
- `asks.take` — 부탁 하나를 연다 — (끝, 그 창에 적을 말). `words` 는 친 말 그대로, `page` 는 누른 창의 파일 이름, `when` 은 말에 넣을 연 때, `tick` 은 작업 폴더 창을 기다리는 동안 거듭 부를 것, `session` 은 이어 갈 대화(없으면 새 대화). VS Code 와 확장 · 작업 폴더 · 주소의 길이를 먼저 보고, 하나라도 아니면 아무것도 안 띄운다.
  - ↑ `vscode_exe`
  - ↑ `has_extension`
  - ↑ `work_folder`
  - ↑ `brief_of`
  - ↑ `link`
  - ↑ `prefill`
  - ↑ `shed_marks`
  - ↑ `raise_folder`
  - ↑ `wait_top`
  - ↑ `bring_forward`
- `press_kinds.due` — 거둘 누름인가 — 아직 안 맺었고, 사내 로그인이 끊겨 못 넣은 것은 `SESSION_RETRY_S` 가 지난 것만(`eager` — 시계 판 — 면 늘).
  - ↑ `edge.pressed_at`
  - ↑ `clock.seoul_now`
- `press_kinds.put_due` — 「일정에 넣기」 누름 하나가 거둘 때인가 — 그 누름(할 일 `settle` 이 받는다) · 아니면 None(`due`).
  - ↑ `due`
- `press_kinds.put_back` — 그 창에 돌려 적을 「일정에 넣기」 칸 — 끝과 말, 맺었으면 맺은 때 · 사내 로그인이 끊겨 못 넣었으면 해 본 때(그 누름은 남아 다시 해 본다).
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
- `press_kinds.away_due` — 「자리 밖에서 보기」 고름이 거둘 때인가 — (켬인가, 고른 때) · 아니면 None. 안 받은 고름만 — 못 부른 고름은 `SESSION_RETRY_S` 뒤에 다시 해 본다(`eager` — 시계 판 — 면 늘).
  - ↑ `due`
- `press_kinds.times_due` — 「보고 시각」 고름(「이대로 바꾸기」)이 거둘 때인가 — (고르신 시각, 그때 보던 시각, 고른 때) · 아니면 None. 시각은 「HH:MM」 꼴만 · 겹침 없이 차례로. 안 받은 고름만(`away_due` 와 같은 다시 해 보기).
  - ↑ `due`
- `press_kinds.said_back` — 스캔의 명령이 고름을 받았나를 그 창에 돌려 적을 칸 — 받은 때 · 그 끝 줄(한 줄로 · `brief_const.SAID_MAX` 에서 자른다) · 안 따랐나.
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
- `press_kinds.ask_due` — 창 머리의 부탁이 거둘 때인가 — (친 말, 누른 창의 이름, 들고 온 세션) · 아니면 None. 안 맡은 부탁이 누른 지 `brief_const.ASK_TAKE_S` 안일 때만 — 그보다 늦은 부탁은 안 연다: 창이 이미 「못 열었다」로 맺었거나 맺는다.
  - ↑ `edge.pressed_at`
  - ↑ `clock.seoul_now`
- `press_kinds.appr_due` — 「결재 창 열기」 누름 하나가 거둘 때인가 — 그 누름 · 아니면 None. 안 맺은 누름이 누른 지 `brief_const.ASK_TAKE_S` 안일 때만(부탁과 같은 까닭 — 늦게 뜬 창은 자리를 뜬 사람을 놀라게 한다). 시계 판은 안 거둔다 — `eager` 를 안 본다.
  - ↑ `edge.pressed_at`
  - ↑ `clock.seoul_now`
- `press_kinds.appr_back` — 그 창에 돌려 적을 「결재 창 열기」 칸 — 맺은 때 · 끝(opened · failed · session) · 말.
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
- `press_kinds.ask_back` — 그 창에 돌려 적을 부탁의 칸 — 맡은 칸에 맺은 때 · 끝 · 말.
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
- `press_kinds.Measure` — 누름 종류 하나의 재는 반 — `key` 창의 저장소 열쇠(끝이 「:」 면 머리 — 누름마다 그 뒤가 열쇠) · `due(누름, 시계 판인가)` 거둘 때면 할 일이 받을 값, 아니면 None · `back(누름, 끝…)` 그 창에 돌려 적을 칸.
- `presses.run_away` — 시계의 켜고 끄는 명령 한 번 — `clock_said` 의 답.
  - `unattended_link.clock_said` — `--chosen-at` 을 준 시계의 명령 한 번 — (따르지 않았나, 그 창에 적을 말). 그 명령은 끝 줄에 그 말만 내고 종료 값으로 따랐나를 댄다(0 따랐다 · 1 안 따랐다). 못 부르거나 끝 줄이 없거나 그 밖의 종료 값이면 (None, 까닭) — 남겨 두어 시계 판이 받는다.
  - ↑ `run_unattended`
  - `unattended_link.away_args` — 「자리 밖에서 보기」를 켜고 끄는 시계 명령의 인자.
- `presses.run_times` — 시계의 창 시각을 거는 명령 한 번 — `clock_said` 의 답. 시계 판이 창의 시각을 받을 때와 같은 자로 재고 건다 — 보던 시각(`base`)에서 더하고 빼신 것만 지금 걸린 시각표 위에 얹고, 그 뒤 대화에서 바꾸셨으면 안 건다.
  - ↑ `unattended_link.clock_said`
  - ↑ `run_unattended`
  - `unattended_link.times_args` — 창에서 고르신 보고 시각을 거는 시계 명령의 인자 — 보던 시각(`base`)에서 더하고 빼신 것만 얹는다(시계 판이 같은 자로 잰다).
- `presses.eul` — 조사 「을/를」 — 끝 글자에 받침이 있으면 「을」.
- `presses.collect_said` — 창의 고름 하나(자리 밖에서 보기 · 보고 시각)를 거둔다 — 거둘 때면 시계의 명령으로 걸고 받았나 · 까닭을 그 창에 적는다.
  - ↑ `edge.stored`
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
  - ↑ `eul`
  - ↑ `state.row`
- `presses.open_ask` — 부탁 하나를 VS Code 에 연다(곁의 `asks.take`) — (끝, 그 창에 적을 말). `tick` 은 기다리는 동안 거듭 부를 것.
  - ↑ `asks.take`
  - ↑ `clock.seoul_now`
- `presses.collect_ask` — 창 머리의 부탁을 거둔다 — 거둘 때면 맡고(창의 값이 그대로일 때만) VS Code 에 연 뒤 끝을 그 창에 적는다.
  - ↑ `edge.stored`
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
  - ↑ `beat_row`
  - ↑ `edge.EdgeGone`
- `presses.start_approval` — 결재 손 open 한 번을 띄우고 기다리지 않는다 — 그 프로세스 · 못 띄웠으면 (None, 까닭). 창 곁의 손은 걸음마다 끝났나만 본다 (`approval_done`) — 열기를 기다리는 동안에도 다른 누름(부탁 · 다른 결재)을 제때 맡는다.
  - ↑ `proc_base.python_argv`
  - ↑ `piped`
- `presses.approval_done` — 띄운 open 이 끝났으면 (끝, 말), 아직이면 None. `C.APPR_OPEN_S` 를 넘기면 끊고 못 띄움으로 맺는다.
- `presses.open_approval` — 누른 결재 문서 하나의 창을 띄우기 시작한다 — 그 프로세스, 또는 바로 맺을 (끝, 말). 누른 창의 보고 글에 링크로 선 문서만 연다 — 창의 저장소는 file: 창끼리 하나라 거기 적힌 id 를 믿지 않는다.
  - ↑ `store.page_brief`
  - ↑ `brief_inline.approvals_in`
  - ↑ `start_approval`
- `presses.collect_approvals` — 「결재 창 열기」 누름을 거둔다 — 거둘 때인 누름마다 맡고(창의 값이 그대로일 때만 — 한 누름은 한 번 띄운다) 결재 손을 띄워 두고, 띄워 둔 것 가운데 끝난 것의 끝을 그 창에 적는다.
  - ↑ `edge.cells`
  - ↑ `clock.stamp`
  - ↑ `clock.seoul_now`
  - ↑ `Borrow`
  - ↑ `approval_done`
  - ↑ `start_approval`
- `task_kinds.count_words` — 사람 수의 말 — 「한」 · 「두」 … 「열」, 열을 넘으면 숫자.
- `task_kinds.ro` — 조사 「(으)로」 — 끝 글자에 받침이 있으면(ㄹ 받침은 빼고) 「으로」. 한글이 아니면 「(으)로」.
- `task_kinds.span_fits` — 두 시각이 일정 손의 꼴(`PUT_STAMP`)이고 시작이 끝보다 앞인가.
- `task_kinds.people_fit` — 사람을 대는 칸(받는 분 · 참석)이 사람 링크로 선 사람들인가.
  - ↑ `brief_people.people_in`
- `task_kinds.span_value` — 넘길 때 — 해까지 든 서울 시각 둘(사람이 읽는 줄은 「11월 19일(목)」로 해가 빠진다).
- `task_kinds.read_fits` — 꼴이 차례로 다 읽힌 것으로 선다(찾아 정리 · 대화) — 값 하나가 비지 않았다.
- `task_kinds.reply_fits` — 답장의 꼴 — 받는 분이 사람 링크이고 답할 메일이 32자리 메일 번호.
  - ↑ `people_fit`
- `task_kinds.mail_fits` — 새 메일의 꼴 — 받는 분이 사람 링크.
  - ↑ `people_fit`
- `task_kinds.room_fits` — 회의실 잡기의 꼴 — 두 시각 · 방이 회의실 링크 · 참석이 사람 링크.
  - ↑ `span_fits`
  - ↑ `people_fit`
- `task_kinds.teams_fits` — Teams 회의의 꼴 — 두 시각 · 참석이 사람 링크.
  - ↑ `span_fits`
  - ↑ `people_fit`
- `task_kinds.put_fits` — 일정 넣기의 꼴 — 칸의 값이 넣을 일정으로 읽혔다(`brief_put.put_of`).
- `task_kinds.find_values` — 찾아 정리가 넘길 값 — 찾을 것.
- `task_kinds.reply_values` — 답장이 넘길 값 — 받는 분 · 답할 메일(메일 링크) · 할 말.
- `task_kinds.mail_values` — 새 메일이 넘길 값 — 받는 분 · 제목 · 할 말.
- `task_kinds.room_values` — 회의실 잡기가 넘길 값 — 때 · 방(회의실 링크) · 제목 · 참석.
  - ↑ `span_value`
- `task_kinds.teams_values` — Teams 회의가 넘길 값 — 때 · 제목 · 참석 · (적었으면 안내).
  - ↑ `span_value`
- `task_kinds.what_line` — 찾아 정리의 줄 — 찾을 것 그대로.
- `task_kinds.say_line` — 대화의 줄 — 할 말 그대로.
- `task_kinds.reply_line` — 답장의 줄 — 「받는 분께 — 무슨 답」.
- `task_kinds.mail_line` — 새 메일의 줄 — 「받는 분께 「제목」 — 할 말」.
- `task_kinds.room_line` — 회의실 잡기의 줄 — 때 · 방 이름 · 「제목」 · 참석.
- `task_kinds.teams_line` — Teams 회의의 줄 — 때 · 「제목」 · 참석 · (적었으면 안내).
- `task_kinds.put_line` — 일정 넣기의 줄 — 무엇을 넣나 · 공개 범위.
- `task_kinds.room_fill` — 회의실 잡기의 무엇이 되나에 채울 칸 — 안내 메일이 갈 분의 수 · 일정에 들 제목과 그 조사.
  - ↑ `count_words`
  - ↑ `ro`
- `task_kinds.span_start` — 때가 든 일의 시작.
- `task_kinds.put_start` — 일정 넣기의 시작 — 넣을 일정의 시작.
- `unattended/brief_day.last_try` — 그날 가장 늦은 살펴보기의 답 — 판 기록에 싣는다.
- `unattended/task_base.template_pattern` — `str.format` 틀을 그 틀로 지은 글을 되읽는 정규식으로 — 글자는 그대로, 칸마다 `forms` 의 꼴을 이름 붙은 묶음으로 잡는다.
<!-- /drawn:piece-map -->

## 흐름 — 사람이 일으키는 일마다

### 보고를 짓고 창을 연다

대화에서 「보고해 줘」 하시거나 시계가 정한 시각에 사람 없이 띄우면 모델이 `lane.md` 의 차례대로 간다: `ticks.py`(창의 표시를 먼저
거둔다) → 업무 파악 → 메일 · 일정 읽기 → 보고 글을 써서 `window.py` 에 준다. 그 뒤는 코드다.

```
window.py ─ decode ─▶ finish.finish ─▶ brief_text.parse ─▶ render.build ─▶ 창 HTML 쓰기 ─▶ 보고 글(.md) 쓰기 ─▶ edge.open_tab ─▶ presses.start_hand
                       │ 지난 보고 글의 기록 절 잇기        │ state.state_of · prefs_file.read · asks.ready
                       │ 「일정 넣기」마다 presses.run_calendar(미리 보기)
```

- **받는 것의 경계** — 보고 글은 `--in` 의 파일, 없으면 표준 입력이다. UTF-8(BOM 이 있어도) · BOM 이 있는 UTF-16 · 그도 아니면 cp949 로
  읽는다 — Windows 도구가 쓴 파일도 받는다. 코드는 `lane.md` 가 정한 꼴(제목 · 절 · 줄 · 메일 번호 · 기한 표지 · 마감 시간줄 · 칸 · 끝의 두
  절)만 읽고, 꼴을 모르는 줄은 문단의 글로 남긴다 — 버리는 줄은 빈 줄과 가름줄(---)뿐이다. 제목이 없으면 창을 짓지 않는다
- **`--dir` 는 한 번만 받는다** — 사람 없는 실행은 `--dir` 까지를 고정한 명령 꼴만 열어 두므로, 뒤에 붙은 둘째 `--dir` 가 이기면 그 경계 밖에
  쓴다. 줄인 이름(`--di`) · `--dir=…` 꼴도 같은 칸이라 함께 걸린다. 없는 폴더는 만들지 않는다
- **`--mailbox`** — 회사 메일 스킬의 `session` 이 낸 메일함 주소(`http(s)://<호스트>/…/<이름>.nsf`). 호스트 앞에 사용자 칸(@)이 서는 꼴 ·
  따옴표 · 빈칸 · 물음표는 받지 않는다. 없거나 꼴이 아니면 메일 줄을 링크 없이 글과 메일 번호로 세운다

#### 보고 글을 마무리한다

창과 남는 보고 글은 마무리한 글 하나에서 선다(`finish.py`). 모델은 판단을 쓰고, 이미 정해진 값은 마무리가 원본에서 들고 와 붙인다.

- **기록 절을 잇는다** — 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」은 사용자가 창에서 누르시거나 대화에서 하신 말씀의 기록이고, 다음
  업무 파악이 가장 늦은 보고 글의 그 절로 일을 닫고 다시 연다. 마무리는 지난 보고 글(이름이 가장 늦은 `brief-….md`)의 두 절을 새 글 끝에
  잇는다 — 새 글의 같은 절에 이미 든 줄(같은 첫 메일 번호 · 번호가 없으면 같은 글)은 안 겹친다. 두 절은 일마다 사용자의 마지막 말씀이다 — 한쪽에
  줄을 더하는 손(거두는 손 · 대화)이 맞은편의 같은 일 줄을 걷어, 같은 메일 번호는 한쪽에만 선다. 그 말씀보다 늦은 메일이 끝을 보이면 업무
  파악이 메일을 따른다(스킬 mailbox-work 「끝난 일」). 「끝났다고 하신 것」은 줄이 없어도 「없음」으로 세운다 — 거두는 손 · 다음 보고가 그
  절을 찾는다. 지난 보고 글이 있는데 못 읽으면 창을 짓지 않는다(`finish.Unread` · 종료 1) — 이을 줄을 모르는 새 글이 가장 늦은 글이 되면
  그 말씀이 사라진다
- **「일정 넣기」에 열쇠를 단다** — 모델은 일정 손 미리 보기 답의 값(시작 · 끝 · 제목 · 곳 · 공개 범위)만 적는다. 마무리는 열쇠 없는 줄마다
  같은 값으로 미리 보기를 불러(`presses.run_calendar` — 일정을 바꾸지 않는다) 받은 열쇠를 그 줄 끝에 달고, 그 판의 그 시각(비었다 · 겹치는
  일정)을 그 카드의 칸들 앞에 점으로 넣는다. 사람이 보는 판과 누른 뒤 넣는 손이 견줄 열쇠가 한 미리 보기에서 나온다. 이미 든 일정이면 열쇠
  없이 그렇다는 점을, 미리 보기를 못 받았으면(세션 · 시한 · 일정 손이 곁에 없다) 대화로 가라는 점을 달고 끝 줄 앞에서 경고한다 — 창은 열쇠
  없는 줄에 단추 대신 그렇다는 말을 단다(`render.PUT_NOKEY`). 열쇠가 이미 적힌 줄은 그대로 둔다. 마무리한 글을 다시 받으면 그 카드의 앞선
  점을 걷고 지금 판의 점 하나만 둔다
- **옛 꼴의 「걸지 않기로 하셨다」** — 맞춤 파일에 그 절이 생기기 전의 보고 글은 그 말씀을 「이 보고가 본 데」의 한 줄로 들었다. 그 절이
  없는 맞춤 파일을 읽는 손(`prefs_file.read`)이 가장 늦은 보고 글의 그 줄을 읽어 들이고, 마무리가 맞춤 파일에 적는다 — 새 보고 글이 가장 늦은
  글이 되는 순간이 지나면 그 말씀이 어디에도 안 남는다. 그 절이 선 파일은 옛 꼴을 다시 안 읽는다

#### 남기고 띄운다

- **보고 글은 창이 선 뒤에만 남긴다** — 다음 보고는 남은 글을 사용자께 낸 보고로 읽는다. 창을 못 지으면 글도 안 남기고, `--dir` 밖에 쓰지
  않는다. 남는 `.md` 는 마무리한 글을 줄끝만 LF 로 맞춘 UTF-8 이다 — 창이 선 그 글이다. 이름이 지은 때(이 PC 의 시각)라 이름 차례가 곧 때의
  차례다
- **창은 로그인 Edge 의 새 탭이 먼저다** — 스킬 ep-login 이 여는 디버깅 포트(`EDGE_DEBUG_PORT` · 쉼표로 여럿이면 첫 것)의 Edge 에 열려야
  메일 링크가 같은 회사 세션에서 로그인 창 없이 열린다. 새 Chromium 은 `/json/new?<주소>` 를 PUT 으로만 받는다. 포트는 이 PC(127.0.0.1)만
  부르고 짧게 기다리며, 어떤 실패든 기본 브라우저로 간다. 그 Edge 로 연 창만 주소에 꼬리 `?via=edge` 를 단다 — 누르신 것은 그 Edge 의 저장소에서만
  거둬진다
- **창 곁의 손을 띄운다** — 로그인 Edge 에 연 창이 거둘 누름을 가질 수 있으면(「일정 넣기」 카드 · 맡길 일이 있다 · 보고가 걸려 「자리 밖에서
  보기」 단추가 선다 · 부탁 칸이 선다 — `hand_wanted.hand_wanted`) 그 곁에 손을 띄운다(아래 「창 곁의 손」). 기본 브라우저로 연 창에는 안 띄운다
- **끝 줄** — 두 파일 · 절 · 줄 · 메일 링크의 수 · 띄웠나를 말하고, 꼴이 틀린 칸 · 빠진 끝의 절 같은 경고가 앞에, 「다음: …」이 뒤에 선다.
  모델은 그 말대로 다음 걸음을 간다

#### 스스로 로그인해 지은 보고의 한 줄

시계가 세션 없이 스스로 로그인해 띄운 보고의 창은 머리(지은 때 아래)에 한 줄을 든다 — 몇 시에 비서가 사내 로그인을 새로 했고, 그래서
평소 Edge 의 메일 · 일정 창이 닫히고 EP 포털에서 앱을 새로 못 띄우며, 이 보고가 끝나고 `GIVE_BACK_AFTER_MIN` 분 뒤 비서가 로그인을 평소 Edge 로 돌려주고 쓰지 않는 EP 탭을 닫는다 — 그 전에 띄워야 하면 사람이 평소 Edge 에서 EP 에 다시 로그인한다(대화의 「EP 돌려줘」는 모델이 듣는 말이라 창에 적지 않는다 · `render.SIGNED_NOTE` · 이미 띄운 앱 창은 그대로 된다 · 아래 「사람의 로그인을 돌려준다」).

- **값은 시계가 적은 것이고 판정은 지은 때다** — 시계는 그 로그인이 선 판에서 시각표 파일의 `signed` 칸에 로그인한 때(`at`)와 그 로그인으로
  띄운 보고가 글을 남길 수 있는 끝(`until` — 띄운 때에서 잰다)을 띄우기 전에 적는다. 지을 때 `state.state_of` 가 그 칸을 읽고(`signed_from` — 시간대를 단 ISO 꼴 둘일 때만),
  그리기(`render.signed_note`)가 지은 때가 그 사이면 줄을 세운다. 모델은 그 줄을 쓰지도 옮기지도 않는다 — 한 번 빠뜨리면 사람이 포털이 왜
  죽었는지 모른다
- **로그인 없이 지은 보고에는 안 선다** — 범위가 지났거나 · 적힌 것이 없거나 · 꼴이 아니면 줄 없이 그대로 짓는다. 그 범위 안에 대화에서 지은
  보고에는 선다 — 줄은 「몇 시에 로그인을 새로 했다」는 사실이라 그 보고에서도 참이다
- 메일 한 장(자리 밖에서 보기)에는 안 싣는다 — 자리 밖에서는 포털에서 앱을 띄울 일이 없다

### 누르신 표시 — 「끝났음 · 내일 다시 · 이런 건 빼기」

창에서 누르신 「끝났음」은 대화에서 「그건 끝났어」를 말씀하신 것과 같은 자리(가장 늦은 보고 글의 「끝났다고 하신 것」)에, 푸신 「끝났음」은
「그거 아직이야」와 같은 자리(「안 끝났다고 하신 것」)에 닿는다. 「내일 다시」 · 「이런 건 빼기」은 보고 맞춤 파일(아래 「보고 맞춤」)에
닿는다 — 일이 끝났나는 업무 파일의 몫이고, 언제 · 무엇을 올리나는 보고의 몫이라 자리를 가른다.

```
report.js(줄의 단추) ─▶ 창의 저장소 brief-done:<메일 번호> ─▶ (다음 보고 · 대화) ticks.py: edge.page → Tab.read
   ─▶ brief_sections.fold(가장 늦은 보고 글) · prefs_file.write(맞춤 파일) ─▶ 옮긴 표시에 남긴 때를 적는다 ─▶ state.sync
```

- **할 일의 줄에는 단추 셋** — 셋 가운데 하나만 눌린다(다른 것을 누르면 그것으로 바뀌고, 눌린 것을 다시 누르면 바탕으로). 「끝났다고 하신
  것」의 줄에는 눌린 「끝났음」 하나뿐이다 — 끝난 일을 미루거나 감출 까닭이 없다. 셋은 줄의 오른쪽 위에 나란히 선다 — 감춘 차림(「⋯」)은
  있는 줄도 모른다
- **열쇠는 그 줄의 일** — 업무 파일은 일을 그 일을 연 메일 번호 · 사람 · 제목으로 잇는다. 줄 · 카드의 `- 일: <메일 링크>` 칸이 그 일의 메일이고
  (`brief_cards.item_key`), 그 칸이 없으면 줄의 첫 메일 번호다 — 카드에 근거 메일이 여럿이면 첫 링크가 그 일의 메일이라는 보장이 없어, 차례에
  기대면 「끝났음」이 엉뚱한 메일로 적혀 업무 파악이 그 일을 못 닫는다. 메일 번호가 든 줄에만 단추가 서고, 「이 보고가 본 데」 · 「안 끝났다고
  하신 것」 · 회의 한 장의 절에는 안 선다. 같은 메일이 두 줄에 서면 두 단추 무리가 함께 움직인다
- **표시는 창의 저장소에 산다** — `brief-done:<메일 번호>` 에 일 이름 · 누른 때 · 무엇을 누르셨나(`mark`)가 든다. 창에는 사용자 폴더에 쓰는
  길이 없어서 거두는 쪽이 그 Edge 에서 읽어 온다. Chromium 은 file: 창끼리 저장소 하나를 써, 탭을 닫아도 · 다른 날의 창에서도 같은 표시가
  보인다
- **언제든 누르고 푼다** — 잠그지 않는다. 잘못 누르셨거나 끝난 일이 다시 살아나도 창에서 바로잡는다. 거둔 표시는 언제 어디로 옮겼나를 말하고,
  열린 창은 거두는 순간 바로 바뀐다. 창을 짓기 전에 거둔 표시는 그 창에서 안 쓴다(`data-made`) — 거둔 것은 그 창의 글에 이미 들었고, 그런데도
  그 일이 할 일로 섰으면 다시 열린 것이다
- **거두는 손(`ticks.py`)** — 로그인 Edge 의 디버깅 포트에 CDP 웹소켓 하나로 붙어(`edge.py` · 표준 라이브러리만 — Origin 을 안 실어
  `--remote-allow-origins` 에 안 걸린다) file: 탭 하나에서 표시를 읽는다. 열린 file: 탭이 없으면 가장 늦은 보고 창을 뒤 탭으로 잠깐 열고 닫는다.
  새로 바뀐 표시만 옮긴다 — 끝났다면 「끝났다고 하신 것」 끝에, 푸셨으면 「안 끝났다고 하신 것」 끝에(없으면 세운다) 한 줄씩 더하고 맞은편
  절의 같은 번호 줄은 걷는다. 미루거나 감추신 일은 맞춤 파일에 옮기고 「끝났다고 하신 것」에서 걷는다(뒤에 누르신 것이 이긴다)
- **두 번 더하지 않는다** — 보고 글과 맞춤 파일을 다 쓴 뒤에만 옮긴 표시에 남긴 때를 적는다. 남긴 때가 적힌 표시는 안 읽고, 갈 절에 이미 든
  메일 번호도 안 더한다 — 보고 글에 쓰고 창에 적기 전에 멈춰도 다음 판이 보고 글을 보고 거른다. 보고 글은 임시 파일에 써서 바꿔 놓는다
- **창의 글은 글자로만 들인다** — 일 이름은 창의 칸에서 온 글이라 줄바꿈 · 꼴 표시 · 메일 번호 꼴을 걷고 줄인다. 걷지 않으면 절 머리가
  생기거나, 다음 업무 파악이 이름 속 번호를 그 일의 메일로 읽어 엉뚱한 일을 닫는다. 줄을 더하면 그 절의 「없음」 한 줄을 걷는다
- **Edge 가 없으면 보고 글을 안 고친다** — 종료 3. 표시는 그 Edge 프로필에 남아 다음 판이 거둔다. 돌아올 날이 된 「내일 다시」를 옮기는 맞춤
  파일 쓰기와 맞춤의 무리(아래)는 그래도 한다
- **푼 표시도 옮긴다** — 거둔 「내일 다시」 · 「이런 건 빼기」을 바탕으로 되돌리면 표시가 `clear` 로 남아 맞춤 파일의 그 메일 줄을 걷는다.
  「끝났음」도 그 메일의 맞춤 줄을 걷는다

### 보고 맞춤 — 보고에서 빼는 것 · 내일 다시 볼 것

사용자 폴더의 `daily-brief-prefs.md` 한 장이 든다 — 업무 파일 곁의, 사람이 열어 읽고 고칠 수 있는 글이다(줄을 지우시면 그대로 따른다). 쓰는
손은 `prefs.py`(대화의 명령) · `ticks.py`(창의 표시) · 옛 꼴의 「걸지 않기로 하셨다」를 옮기는 마무리이고 꼴은 `prefs_file.py` 한 자리가 든다. 업무 파일에 두지 않는 까닭 — 일이 무엇이고
끝났나는 업무 파악의 사실이고, 무엇을 올리나는 이 사람이 보고에 바라는 것이다. 메일함 정리도 업무 파일을 읽어, 거기 섞으면 「이런 건 빼기」이
정리의 판단까지 굽힌다. 메일함 규칙 · 폴더로도 안 바꾼다 — 보고에 안 올릴 뿐이다.

- **「보고에서 빼는 것」** — 줄마다 보기 하나다: 창에서 누르신 일은 그 일 이름 · 날 · 보기 메일, 대화의 말은 사용자의 말 그대로. 보고는 같은
  갈래(같은 보낸 곳의 정기 메일 · 같은 꼴의 알림)를 올리지 않고 「이 보고가 본 데」에 그 수만 적는다 — 갈래를 가르는 것은 모델이다(누름 하나는
  「이런 것」의 보기일 뿐 규칙을 담지 못한다). 줄의 열쇠는 메일 번호, 없으면 글의 지문이다 — 창의 「다시 넣기」가 이 열쇠로 그 줄을 짚는다
- **「내일 다시 볼 것」** — 줄마다 돌아오는 날(누르신 날의 다음 날 · 이 PC 의 날)을 `YYYY-MM-DD` 로 든다. 거둘 때마다 `ticks.py` 가
  가른다(`prefs_file.take_due`): 그날이 오늘이거나 지났으면 「다시 올린 것」으로 옮기고 「돌아온 것」으로 낸다 — 그 전에는 「미룬 것」이다. 날이
  꼴이 아닌 줄은 돌아온 것으로 본다 — 미룬 채 잊히지 않게
- **「다시 올린 것」** — 돌아와 보고에 댄 줄과 그 때. 그 때나 그 뒤에 지은 보고 글이 있으면 다음 거둠이 걷고, 없으면 거둘 때마다 또
  「돌아온 것」으로 낸다 — 거두기만 하고 보고가 안 지어진 판(세션이 끊겼다 · 맡긴 쪽이 멈췄다)에도 그 일이 사라지지 않는다. 창의 「내일 다시 볼
  것」 목록에는 안 선다
- **「걸지 않기로 하신 것」** — 처음 보고 때 여쭌 아침 보고를 마다하신 말씀(`prefs.py decline` — 옛 판에서는 메일함 스캔도 함께 여쭈었다).
  시계나 보고 예약이 없으면 대화가 이 줄을 보고 다시 여쭙지 않는다. 그 줄을 지우시면 다음 보고 때 다시 여쭙는다
- **보고가 받는 길** — `ticks.py` 가 끝 줄 앞에 「보고에서 빼는 것 · 돌아온 것 · 미룬 것」 무리와 지난 보고 뒤의 「일정에 넣기」 · 맡기신 일의
  끝을 낸다(Edge 에 못 닿아도). 보고를 짓는 쪽은 이 출력을 읽는다 — 파일을 따로 열거나 봉투에 옮겨 적을 일이 없다

### 보고 맞추기 — 창 끝의 칸

창 끝에 넷이 선다: 보고 시각 · 자리 밖에서 보기(보고가 걸렸을 때만) · 보고에서 빼는 것(줄마다 「다시 넣기」) · 내일 다시 볼 것. 보고
글의 사실이 아니라 사용자 폴더의 지금 모습이라 보고 글의 절로 세지 않는다. 시각표와 「자리 밖에서 보기」의 주인은 시계(`unattended/`)다 — 창은
고르신 것을 남기고, 거는 것은 시계의 명령이다.

```
report.js ─▶ brief-times · brief-away ─▶ presses.watch: 누름 종류 표의 그 줄 → presses.run_unattended(clock.py window-times · away … --chosen-at <고른 때>) ─▶ 끝 줄을 그 창에
             (손이 없으면) 시계 판 ─▶ window_door.read_choices(함수) ─▶ 시계가 재고 건다 ─▶ ticks.py --times-done · --away-done 으로 그 창에
```

- **창이 보이는 지금 모습** — 지을 때 `state.state_of` 가 사용자 폴더의 시각표(시각 하나를 쓰던 옛 꼴도) · 시계의 마지막 판 · 맞춤 파일의 두 절에서
  짓고 창에 박는다(`data-state`). 그 뒤에는 그것을 바꾸는 손 — 대화의 `clock.py` · `prefs.py`, 시계 판, 거두는 손 — 이 열린 file: 탭에만
  적는다(`brief-state` · 탭을 안 연다). 한 줄은 `state.row` 한 자리에서 짓고, 이미 붙은 창에는 그 손이 바로, 대화의 명령 뒤에는
  `state.sync`(`window_link.tell_window`)가, 시계 판은 고름을 읽는 창의 문(`window_door.read_choices`)이 함께 적는다. 창은 둘 가운데 늦은 것을 보이고 그 모습이 언제
  것인지를 늘 댄다. 못 읽은 파일은 「없습니다」로 안 보이고 무엇을 못 읽었나를 댄다
- **창의 고름은 「한 일」이다** — 「이대로 바꾸기」는 그때 보던 시각과 고른 시각을 함께 남기고, 시계는 보던 시각에서 더하고 빼신 것만 지금
  걸린 시각표 위에 얹는다 — 창이 보여 드리지 않은 시각(그 사이 대화에서 더한 것)은 안 빠진다. 걸린 때보다 앞서 고르신 것은 낡았다고 말하고
  안 건다 — 나중의 말씀(대화)이 이긴다. 아직 안 걸린 시각에는 「걸기 전」이 붙는다
- **더하실 때 바로 잰다** — 시각끼리 몇 분을 띄어야 하나 · 시각마다 얼마나 기다리나의 수는 시계가 들고, 시각표를 걸며 그 파일에 함께
  적는다(`room_min` · `wait_min`). 창은 그 수로 더하실 시각을 재고(셈은 시계의 틈 셈과 같은 `crowded`) 모자라면 그 자리에서 안 더한다.
  수를 못 받은 창은 재지 않고 비서가 받을 때 잰다고 말한다. 시계가 받을 때 다시 재고, 걸지 않은 시각을 다 까닭과 함께 · 건 것을 사실대로
  적는다
- **창 곁의 손이 바로, 없으면 시계 판이** — 손은 고름을 보는 대로 시계의 명령으로 걸고 그 끝 줄을 그 창에 돌려 적는다. 손이 없으면 시계
  판마다 같은 고름을 같은 자로 받는다(아래 「보고 창에서 고르신 것을 받는다」). 두 길이 같은 고름을 함께 봐도 고른 때가 같으면 둘째는
  이미 받은 것으로 지나간다. 다음 보고를 기다리지 않는 까닭 — 아침에 더하신 13:00 은 13:00 전에 보고가 없어 그날 안 선다
- **자리 밖에서 보기 — 켜고 끄는 단추 하나** — 켜 두면 사람 없이 지은 보고가 칸마다 한 통 본인 메일로 간다. 고른 것이 곧 동의라 따로 묻는
  칸이 없다. 켤 때 본인 주소는 시계가 주소록의 「나」에서 받고, 못 받으면 켜지 않고 까닭을 그 창에 적는다. 받는 분 줄은 지금 모습에서만 선다 —
  창에서 주소를 받는 칸은 없다. 받기 전에 다시 누르면 고름을 지운다
- **누른 직후의 말은 창이 고른다** — 손의 숨 표가 살아 있으면 「곧」, 끊겼으면 「다음 확인에」, 시계도 한동안(`FRESH_SCAN_MS`) 안 돌았으면
  대화로 가라고 말한다. 대화의 되돌림도 따른다 — 거둔 「내일 다시」 · 「이런 건 빼기」이 지금 모습에 없으면 그 줄의 단추와 말을 바탕으로
  돌린다. 이 창에서 「이런 건 빼기」을 누르시면 「보고에서 빼는 것」에 그 일이 바로 선다

### 일정에 넣기

「일정 넣기」 줄 하나가 넣을 일정 하나다(맡길 일의 한 종류). 사람이 그 줄을 누른 것이 그 한 건의 확인이다 — 줄이 미리 보기의 판(값 · 공개
범위 · 그 시각의 겹침 · 누르면 무엇이 되나)을 다 보였기 때문이다. 무엇을 붙이나는 모델이 정하고(`lane.md` 「무엇이 내 약속인가」), 넣기는
코드만 한다 — 사람 없는 보고도 미리 보기(바꾸지 않는다)까지만 부른다. 그래서 이 줄은 막대의 「표시한 n건 맡기기」에 함께 들어도 맡길 일의
누름에 안 들고, 누르자마자 제 누름을 남긴다.

```
report.js ─▶ brief-cal:<열쇠> ─▶ presses.put_presses(OS 잠금 · 기록) ─▶ settle ─▶ card_for(누른 창의 보고 글에서 그 열쇠의 카드) ─▶ run_calendar(일정 손 add)
   ─▶ outcome ─▶ 끝과 말을 그 창에                           (손이 없으면 시계 판의 ticks.py --presses 가 같은 표의 줄로)
```

- **보인 글과 드는 값이 한 자리에서 나온다** — 칸 「바로 할 일: 일정 넣기 | …」(옛 꼴 「넣을 일정」도 읽는다)이 미리 보기 답의 값을 들고, 열쇠는
  마무리가 붙인다. 창은 그 칸을 `brief_put.put_of` 로 읽어 사람이 읽는 줄과 단추로 세우고, 넣는 손은 누름이 가리키는 창의 보고 글(같은
  이름의 .md)에서 같은 함수(`brief_tasks.cards_of`)로 그 열쇠의 카드를 찾아 그 값으로 부른다. 누름은 열쇠 · 누른 때 · 누른 창의 이름만 든다.
  칸의 꼴이 틀리면 단추 대신 그렇다는 말이 선다
- **열쇠가 그 사이의 바뀜을 막는다** — 일정 손은 판을 다시 지어 열쇠가 다르면 `moved` 로 안 넣는다(형제 스킬 company-calendar). 넣는 손은
  열쇠를 견주지 않는다 — 판을 짓는 쪽이 그 손이라 견줌도 그 한 자리에 있다. `moved` 의 답이 낸 지금 판의 열쇠로 다시 부르지 않는다 — 사람이
  못 본 판이다. 그 답의 판이 「이미 있음」을 들면 이미 있음으로 읽는다
- **한 누름은 한 번** — 넣는 길이 둘(창 곁의 손 · 시계 판)이라 같은 누름을 함께 볼 수 있다. 사용자 폴더의 기록(`records.LEDGER_FILE`)을 OS
  잠금(`LEDGER_LOCK`) 아래에서 고친다: 부르기 전에 그 열쇠를 「넣는 중」으로 굳히고 끝을 받으면 그 끝으로. 이미 맺은 누름은 창에 적은 끝이
  사라져도 다시 안 넣는다. 같은 열쇠의 새 누름은 새로 부른다 — 일정 손이 판을 열쇠부터 견줘 이미 든 일정이면 이미 있음으로 답하고, 창은
  맺은 카드의 단추를 잠근다. 잠금을 쥐고 「넣는 중」을 만나면 앞 손이 넣다 죽은 것이라 「확인 안 됨」으로 맺는다 —
  넣고 나서 죽었으면 다시 넣는 순간 두 벌이다. 일정 손이 시한을 넘기거나 모르는 답을 내도 같다. 시각으로 푸는 잠금은 안 쓴다 — 죽은 손을
  「도는 중」으로 잘못 읽어 「바로」가 그만큼 늦는다
- **넣은 기록은 더 나쁜 끝으로 안 덮는다** — 저장소가 file: 창끼리 하나라 넣은 카드를 다른 창에서 또 누르면 같은 열쇠의 누름이 다시 선다.
  앞서 넣은 열쇠의 새 누름이 넣음 · 그 사이 바뀜이 아닌 끝을 받으면 앞의 넣음을 그대로 돌려 적는다. 기록은
  `LEDGER_KEEP_DAYS` 가 지난 줄을 걷는다 — 「한 번」은 그 안에서 선다. 창은 그 창을 짓기 전에 맺은 누름을 카드에 안 쓴다 — 지운 일정을 다음 보고가
  같은 판으로 다시 세운 카드는 처음부터 누를 수 있어야 한다
- **다시 해 보는 것** — 사내 로그인이 끊겨 못 넣은 누름은 맺지 않고 남긴다(로그인하지 않는다). 창 곁의 손은 `press_kinds.SESSION_RETRY_S` 마다, 시계 판은
  판마다 다시 해 본다. 시작이 지난 약속은 부르지 않는다
- **또 눌러도 안 될 끝은 단추를 잠근다** — 넣음 · 이미 있음 · 지난 약속 · 그 사이 바뀜 · 확인 안 됨. 시작이 이미 지난 카드는 누르기 전부터
  잠긴다. 메일에 시각이 없는 카드는 단추 대신 대화에서 시각을 말해 달라는 말이 선다(`NO_TIME_SAID`)
- **끝마다의 말** — 넣는 손이 끝과 그 말을 그 창에 돌려 적는다(`presses.WORDS`). 창이 스스로 고르는 말은 누름 직후 · 손이 없을 때 · 지난 카드 ·
  거둘 수 없는 창뿐이다. 지난 카드의 말은 종류 표(`task_kinds.CAL.late`) 하나가 들고 창은 그 줄의 `data-late` 로, 넣는 손은 지난 약속을 맺을
  때 같은 값으로 쓴다 — 누르기 전과 누른 뒤의 말이 같다. 「다시 누르시면 취소」는 누름이 정말 기다리는 때(손이 없다 · 사내 로그인이 끊겼다)에만 붙는다
- **회의 한 장에는 누름 단추가 없다** — 머리가 `[절 이름](section:meetings)` 인 절(`brief_sections.is_meetings`)의 카드는 회의라 일이 아니다 — 그
  안의 메일 링크로 단추가 서면 회의를 「끝났음」으로 누른 것이 요청 메일의 일을 닫는다. 절의 종류를 이름 글자로 읽지 않는다 — 모델은 그날에
  맞게 이름을 바꿔 쓴다. 표지 없이 쓴 글은 이름이 「오늘 · 내일 회의」(`MEETING_SECTION`)로 시작하는 절을 회의 한 장으로 읽는다

### 맡길 일

보고를 짓는 모델이 카드마다 그 건에서 할 일과 그 갈래(「바로 할 일」 · 「대화로 할 일」)를 적고(`lane.md` 「맡길 일」), 창은 적힌 것을 보이고
누름을 남긴다. 무엇을 · 어느 갈래로 · 어느 방으로는 모델의 판단이고, 창과 손은 그 판단을 다시 하지 않는다. 사람이 창에서 누른 것이 그 줄
그대로 끝까지 하라는 승인이다 — 누른 뒤 묻는 단계 · 경고가 없다.

```
report.js ─▶ brief-run:<창 이름>~<ms> ─▶ runs.Runs.take(창에 맡았다 · 기록에 「넘기는 중」) ─▶ hand_over · launch: unattended/handed.py start
   ─▶ FOLLOW_S 마다 handed.py show ─▶ 일마다 brief-task:<창 이름>/<번호> · 판이 끝나면 그 누름에 끝
```

- **줄은 적힌 값 그대로 선다** — 창(`brief_tasks.task_of` — 종류의 줄은 `task_kinds`)은 그 줄의 꼴(`Kind.fits`)로 칸의 수 · 시각의 꼴 · 메일 번호 · 사람과
  방의 링크를 대 보고, 맞으면 사람이 읽는 줄(`Task.line`)과 무엇이 되나(종류가 정하는 말 · `Kind.cons`)를 세운다. 모르는 종류 · 틀린 꼴은 단추 없이
  적힌 글 그대로와 그렇다는 말을 달고 끝 줄 앞에서 경고한다 — 종류를 짐작하거나 줄을 고치면 사람이 못 본 값을 승인한 꼴이 된다. 회의실 줄은
  날 · 시작–끝 · 방(회의실 링크) · 제목 · 참석자(사람 링크)를 다 들어야 선다 — 누르면 그 분들께 안내 메일이 간다
- **추천은 보고 하나에 하나** — 「대화로 할 일 … | 추천」이 꼭 하나일 때만 창 머리의 칸에 흐린 글로 선다. 둘 넘게 적혔으면 아무것도 안
  올리고 경고한다 — 하나를 고르면 짐작이다
- **카드의 근거는 창을 지을 때 말로 짓는다** — 「대화로 열기」 · 추천이 남기는 부탁의 말은 줄 · 카드 머리 · 칸의 맨글자다(`Task.words`).
  「대화로 이어 가기」는 거기에 결과의 멈춘 까닭과 이어 갈 세션을 창의 스크립트가 붙인다. 창 곁의 손은 그 말에 보고 이름과 경로를 붙여
  연다(아래 「비서에게 부탁하기」). 추천은 부탁 칸이 서는 PC 에서만 선다
- **막대는 두 자리 · 한 몸** — 머리 칸 아래(처음엔 접힘)와 마지막 카드 뒤. 표시 칸은 카드의 줄과 목록의 줄이 한 몸이고, 표시는 이 창에서만
  산다(맡기기 전의 고름이라 남기지 않는다). 맡긴 뒤 막대는 지금을 표지 하나와 한 줄로 말하고, 결과의 말은 카드에만 선다. 시작이 지난 회의실 ·
  Teams 줄은 누르기 전부터 표시가 풀리고 잠긴다. 표시해 맡길 줄이 남지 않았고 막대가 말할 거리(따로 맡긴 줄의 지금)도 없으면 막대와
  그리로 가는 닻이 안 선다 — 누를 것이 없는 단추를 세우지 않는다
- **손은 나르기만 한다**(`runs.py`) — 누름의 일들을 같은 스킬의 사람 없는 실행 `unattended/handed.py start` 에 명령으로 넘긴다. 넘기는 것은 사람이
  카드에서 읽은 줄(`Task.line`), 카드 제목, 보고 글에 적힌 그대로의 카드 머리 · 낱낱 뒤에 그 일의 값을 칸마다 「이름: 값」 한 줄씩
  붙인 것(`Task.run_lines`)과 결과의 이름표(`Kind.labels`)다 — 실행이 사람이 읽은 줄에서 값을 되살리거나 근거 메일이 여럿인 카드에서
  답할 메일을 짐작하지 않는다. 결과는 실행이 꼴대로 썼으면 그 칸을 그대로, 아니면 온 글을 그대로 싣는다 — 문장을 걷거나 고쳐 꼴을 맞추지
  않는다. 실행이 못 맡는다고 답하면 그 까닭을 사람의 말(`runs.CANNOT`)로 적는다. 아무것도 안 바꾸는 종류(`Kind.read_only`)가
  「확인 안 됨」으로 맺었으면 「못 함」으로 적는다
- **한 일은 한 번** — 사용자 폴더의 기록(`records.RUNS_FILE`)이 누름마다 넘긴 판과 일마다의 끝을 든다. 넘기기 전에 「넘기는 중」을 적고, 기록을
  못 읽거나 못 쓰면 넘기지 않는다. 같은 보고의 같은 일이 도는 판에 들었거나 됨 · 여쭐 것 · 확인 안 됨으로 맺었으면 새 누름은 그 판을
  따른다 — 실행은 손과 따로 돌아, 다시 넘기면 같은 방이 두 번 잡히고 안내 메일이 두 번 간다. 다시 넘기는 것은 「못 함」으로 맺은 일과 넘긴 적 없는 일뿐이다
- **창에 적는 것은 기록에서 지은 모습뿐이다** — 걸음마다 기록에서 누름 · 일의 칸을 짓고 저장소와 다른 칸만 적는다. 손이 죽었다 다시 떠도,
  창을 닫았다 열어도 끝이 바로 선다. 맡긴 판이 도는 동안 손은 열린 창이 없어도 남아 끝을 기록에 받는다
- **창은 듣지 못한 끝을 짓지 않는다** — 맡은 누름의 손과 연락이 끊기면 창이 아는 것은 그것뿐이다 — 뒤의 실행은 그때도 회의실을 잡고 답장을
  저장한다. 그래서 끝이 적힌 일은 적힌 그대로, 못 들은 일은 「알 수 없음」, 막대는 「연락 끊김」과 보고를 다시 띄우는 길을 말하고 다시
  맡기기를 내지 않는다. 창에 맡았다고 적혔는데 손의 기록에 없는 누름은 넘긴 것이 없어 손이 아무것도 못 넘긴 누름(`refused`)으로 맺는다 — 일마다
  「못 함」, 막대는 「못 맡김」(`Runs.orphans`)
- **손이 없을 때 맺은 누름을 손이 이어받는다** — 창이 nohand · noanswer 로 맺은 누름도 그 일이 다 이 손이 넘긴 판에 들었거나 다시 넘기면
  안 될 끝이면, 손이 그 판을 따르는 누름으로 받아 맺음을 걷는다(`Runs.adopt`)
- **넘겼는지 모르면 「확인 안 됨」** — 넘긴 답을 못 받으면 도는 판의 목록(`handed list`)에서 그 누름의 판을 찾고, 없으면 「확인 안 됨」으로
  맺는다. 도는 판의 기록을 오래 못 읽어도 같다. 기록은 맺은 지 `RUNS_KEEP_DAYS` 가 지나면 걷는다
- **다음 보고가 끝을 안다** — `ticks.py` 가 끝 줄 앞에 지난 보고 뒤 맡기신 일마다 그 끝과 결과 글의 첫머리를 낸다(`report_reads.run_lines`) — 된
  일을 다음 보고가 또 붙이면 같은 방 · 같은 답장이 둘 선다

창과 창 곁의 손 사이의 저장소 칸은 아래 표가 원본이다(열쇠의 머리 값은 `brief_const`). 손은 누름의 번호를 누른 창의 보고 글에 대어
`brief_tasks.tasks_of` 로 그 줄을 읽는다 — 일의 번호는 카드 머리 · 칸의 차례 · 칸의 글에서 낸 해시라(`TASK_ID_LEN` · 한 보고 안에서 겹치면
「-n」) 같은 글이면 창과 손이 같은 번호를 낸다.

| 열쇠 | 쓰는 쪽 · 때 | 칸과 뜻 |
|---|---|---|
| `brief-run:<창 이름>~<누른 때(ms)>` | 창 — 누를 때 한 번 | `at` 누른 때 · `brief` 누른 창의 파일 이름 · `ids` 할 일의 번호를 할 차례대로(「일정 넣기」 줄은 안 든다) · `cal` 같이 누른 「일정 넣기」 줄의 번호(창의 그림만 쓴다) · `how` batch(표시한 것) · card(그 줄 하나) · again(못 한 것 다시) |
| 같은 열쇠 | 창 곁의 손 — 맡을 때 · 다 했을 때 | `taken` 맡은 때 — `ended` 가 없고 누른 지 `brief_const.RUN_TAKE_S` 안이고 창의 값이 그대로일 때만 맡는다. 맡은 동안 숨 표를 `brief_const.HAND_BEAT_S` 마다 적는다. `ended` 맺은 때(따르기만 한 누름은 따르는 판들이 맺은 때) · `end` done · session(사내 로그인이 끊겨 멈췄다) · stopped(도중에 멈췄다) · refused(아무것도 넘기지 못했다 — 까닭은 일마다) · `said` 덧말. 판이 아직 도는데 맺음이 적혀 있으면 걷는다 |
| 같은 열쇠 | 창 — 손이 없을 때 | 누를 때 숨 표(`brief_const.HAND_KEY`)가 끊겼으면 그 자리에서 `end` nohand. 누른 지 `RUN_TAKE_S` 안에 `taken` 이 없으면 noanswer. 맡은 뒤 숨 표가 끊기면 맺지 않는다 |
| `brief-task:<창 이름>/<일의 번호>` | 창 곁의 손 — 일마다 시작 · 끝 | `run` 그 누름(열쇠의 `<창 이름>~<ms>`) · `state` doing · done · asked(여쭐 것) · failed(못 함) · unsure(확인 안 됨) · `at` 그 상태가 된 때 · `said` 결과의 글(줄바꿈이 문단) · `items` `[{label, unid, note}]`(32자리 번호에서만 링크) · `facts` `[[이름, 값]]` · `more` 회색 끝말 · `session` 여쭐 것 · 확인 안 됨일 때 이어 갈 세션 |
| `brief-ask` | 창 — 「대화로 열기」 · 추천 · 「대화로 이어 가기」 | 머리 칸의 부탁과 같은 기록에 `task` 그 일의 번호 · `session` 이어 갈 세션이 더 든다. `session` 이 이 손이 넘긴 판의 세션이면 그 대화를 이어 연다. 확장은 프로그램이 돌린 세션(`claude -p` 의 `sdk-*`)을 목록에서 빼 그 주소로 못 찾으므로, 판을 띄우는 쪽(같은 스킬 `unattended/handed.py` 의 `ENTRYPOINT` — 값 `daily-brief-handed`)이 사람이 이어 갈 대화라는 이름을 세션에 적는다 |

일의 지금은 상태에서 끌어낸다 — 그 일을 든 가장 늦은 누름과 그 일 기록: 기록이 done · asked · failed · unsure 면 그것 · 누름이 맺혔는데 기록이
없으면 nohand · noanswer 는 「못 맡김」, 그 밖은 「못 함」(doing 에서 맺혔으면 「확인 안 됨」) · 맺히지 않았는데 손과 연락이 끊겼으면 「알 수
없음」 · 아니면 doing 은 「하는 중」, 기록이 없으면 「기다림」. 「확인 안 됨」을 「못 함」에 섞지 않는다 — 다시 맡기면 같은 방이 두 번 잡힌다.
「안 한 n건 다시 맡기기」는 「못 함」과 손이 받을 수 있게 된 「못 맡김」만 다시 맡기고, 「확인 안 됨」 · 「알 수 없음」은 안 맡긴다.

### 비서에게 부탁하기

보고를 보다가 떠오른 일을 창 머리의 칸에 친다. 누르면 그 말이 채워진 Claude Code 대화가 VS Code 의 작업 폴더 창에 열리고, 엔터는 사람이
친다 — 말을 보내는 길은 짓지 않는다(보내기 전에 고칠 자리이기도 하다). 코드는 친 말을 읽어 무엇을 가르지 않는다.

```
report.js ─▶ brief-ask ─▶ presses: collect_ask(창의 값이 그대로일 때만 맡는다 — Tab.swap) ─▶ asks.take: 첫마디 · 두 번 인코딩
   ─▶ raise_folder(Code.exe <작업 폴더>) ─▶ 맨 위 VS Code 창이 그 폴더를 대기를 본다 ─▶ vscode://anthropic.claude-code/open?prompt=… ─▶ 앞에 세운다
```

- **여는 것은 창 곁의 손뿐이다** — 시계 판은 부탁을 안 거둔다 — 손이 없을 때 다음 시계 판에 VS Code 가 뜨면 자리를 뜬 사람이 놀란다. 그래서 창은
  손의 숨 표가 끊겼으면 남기지 않고 그 자리에서 손이 멈춰 있다고 말하고, 누른 지 `ASK_TAKE_S` 안에 손이 안 맡으면 「답하지 않았다」로 맺어
  둔다. 손도 그보다 늦은 부탁은 안 연다 — 다시 뜬 손이 맺은 부탁을 열지 않는다. 맡은 손은 VS Code 를 기다리는 동안에도 숨 표를 적는다.
  맡은 부탁이 `ASK_OPEN_CEILING_S` 에 `ASK_TAKE_S` 를 더한 때 안에 안 맺으면 창은 열렸는지 확인하지 못했다고 말한다
- **한 번에 하나** — 여는 동안 칸과 단추가 잠긴다. 열면 칸이 비고, 못 열면 친 말이 칸에 남아 다시 누르실 수 있다
- **첫마디는 손이 보고 글에서 짓는다** — 친 말, 빈 줄, 어느 보고 창에서 보낸 부탁인가, 그 보고 글의 경로. 보고 이름과 경로는 누른 창의 보고
  글에서 온다 — 창의 저장소는 file: 창끼리 하나라 거기 적힌 값을 믿지 않는다. 친 말만은 사람의 말이라 창에서 온다
- **작업 폴더 창에 연다** — VS Code 는 주소를 마지막으로 올라온 창에 연다(꺼져 있었으면 지난번 창을 되살려 거기). 그래서 손은 `Code.exe <작업
  폴더>` 로 그 창을 맨 위에 세우고, z 차례 맨 위 창의 제목이 그 폴더를 대는 것을 본 뒤 주소를 연다 — 정한 시간으로 기다리지 않고 그 상태를
  보며, 끝내 안 서면 천장(`ASK_OPEN_CEILING_S`)에서 멈추고 까닭을 적는다. 제목에 폴더가 서는 것은 VS Code 설정 `window.title` 의 기본값 덕이다.
  손은 VS Code 를 띄우기 전에 물려받은 세션 표지(`CARRIED_MARKS`)를 제 환경에서 걷는다 — 이 PC 의 Claude Code 세션 표지가 꺼져 있던 VS Code 로
  넘어가면 그 터미널의 claude 가 세션 안의 세션으로 읽고, `ELECTRON_RUN_AS_NODE` 를 든 Code.exe 는 창을 안 띄운다
- **주소는 하나 · 두 번 인코딩** — 확장은 VS Code 가 한 번 푼 query 를 다시 풀어, 한 번만 인코딩하면 `&` 에서 잘리고 `+` 는 빈칸이 되고 `%` 가
  끼면 한글까지 깨진다. 이어 가기면 앞에 `session=<번호>&` 가 선다. 주소가 Windows 명령 줄 한도(`URL_MOST`)에 걸리면 안 열고 줄여 달라고
  말한다
- **앞에 세우기** — 연 뒤 그 창을 `SetForegroundWindow` 로 앞에 세워 본다. Windows 가 막으면 `FlashWindowEx` 로 작업 표시줄 단추를 깜빡이고 창이
  그렇다고 말한다. 흉내 낸 입력 · 앞 창 잠금을 피해 가는 길은 안 쓴다
- **열 수 있나는 찾아서 안다** — VS Code 는 등록된 `vscode:` 처리기에서, 확장은 VS Code 가 고르는 차례(`VSCODE_EXTENSIONS` · 홈의
  `.vscode/extensions`)대로, 작업 폴더는 설치기가 심는 사용자 환경값 `PAISETUP_WORK` 에서 읽는다(레지스트리의 사용자 값을 먼저 · 그다음 프로세스
  값 — 값을 심기 전에 뜬 손은 옛 환경을 든다). 경로를 손에 박지 않는다. VS Code 나 확장이 없는 PC 는 창을 지을 때부터 칸 대신 그렇다는 한 줄이
  선다
- **「열었습니다」는 주소를 그 창에 보낸 데까지다** — 탭이 실제로 섰는지는 손이 모른다. 끝마다의 말은 `asks.WORDS` 가 든다

### 사람별

「누가 나를 기다리나 · 내가 누구를 기다리나」를 보고 글의 줄들에서 한 번 더 세운다 — 새로 읽는 것도, 모델이 따로 쓰는 글도 없다. 줄 끝의
칸 「기다리는 분」 · 「답 주실 분」이 사람을 대고, 그리기가 사람마다 그 줄들로 가는 닻 링크를 모아 두 칸으로 세운다. 할 일의 줄만 센다 —
「끝났다고 하신 것」의 사람은 이제 안 기다린다. 사람을 댄 줄이 없는 날은 안 선다. 모델이 사람별 절을 따로 쓰게 하지 않는 까닭 — 같은
사실을 두 자리에 쓰면 한쪽만 고쳐져 어긋난다.

- **사람은 구조로 온다 — 글을 갈라 찾지 않는다** — 회사 손은 사람을 이름과 주소로 낸다. 보고 글은 그것을 메일 링크와 같은 꼴의 사람 링크
  `[이름 직함](person:<주소>)` 로 싣고(`brief_people.people_in`), 칸은 그 링크를 「 · 」로 이은 것 · 덧말은 링크 바로 뒤 괄호다. 링크만 사람이다 —
  덧말 속 「 · 」를 사람의 가름으로 읽으면 없는 사람이 선다
- **한 분은 주소 하나** — 주소로 묶고 처음 적힌 이름을 보인다. 같은 분이 직함 · 덧말을 달리해 적혀도 한 줄이다
- **꼴이 아닌 칸은 글로만 선다** — 링크 밖의 글이 섞인 칸은 사람별에 안 들고 그렇다는 말(`PEOPLE_BAD`)을 달고 끝 줄 앞에서 경고한다
- **맡길 일의 사람 · 방도 같다** — 회의실 · Teams 회의의 참석 칸과 답장 · 새 메일의 받는 분은 사람 링크, 회의실 잡기의 방은 회의실 손의 id 를
  든 회의실 링크 `[방 이름(정원)](room:<id>)` 라야 그 줄이 선다(`ROOM_CELL`). 안내 메일이 갈 분의 수는 링크의 수다. 창 곁의 손은 그 칸들을
  적힌 그대로 뒤의 실행에 넘겨 실행이 방과 사람을 다시 찾지 않는다
- **사람 링크 전의 꼴로 지은 보고 글** — 다시 짓는 손은 없다. 창 곁의 손이 그 글에서 맡길 일을 찾으면 참석자 칸이 꼴이 틀린 줄로 읽혀 그 일은
  맡지 않고 그 카드에 까닭을 적는다. 메일 한 장은 사람을 이름 글로만 세워 그대로 선다

### 결재 창 열기

보고 글의 결재 문서 링크 `[보일 글](approval:<문서 id>)` 곁에 창이 「결재 창 열기」를 단다. 값(결재하실 것 · 올리신 결재 · 결재선)의 주인은 형제
스킬 company-approval 이고 보고는 읽기만 한다 — 그 스킬은 이 스킬을 싣지 않는다. 누르면 창 곁의 손이 그 스킬의 `approval.py open <id>` 로 문서
창을 사람의 평소 Edge 에 띄우고, 결재 · 반려 · 상신은 사람이 그 창에서 한다.

```
report.js ─▶ brief-appr:<문서 id> {at, brief} ─▶ presses.collect_approvals(창의 값이 그대로일 때만 맡는다 — Tab.swap) ─▶ open_approval
   ─▶ 누른 창의 보고 글에 그 링크가 있나 ─▶ approval.py open <id> 를 띄워 두고(Hand.opening) 걸음마다 끝났나 본다
   ─▶ 그 칸이 맡은 값 그대로면 {state, said, done} 을 그 칸에(Tab.swap)
```

- **기다리지 않는다** — open 은 세션 받기 · 결재함 훑기로 길게 걸린다(`APPR_OPEN_S`). 손이 그동안 멈추면 부탁 · 다른 결재 누름이 맡는 틈
  (`ASK_TAKE_S`)을 넘겨 「답하지 않았다」로 맺힌다. 그래서 띄워 두고 걸음마다 끝만 본다. 창은 `APPR_OPEN_S` 에 맡는 틈을 더한 때까지 기다린 뒤에야
  「확인하지 못했다」고 말한다
- **끝은 새 누름을 덮지 않는다** — 그 사이 다시 누르신 누름이 그 칸에 서 있으면 끝을 안 적는다

- **부탁과 같은 울타리** — 창 곁의 손만 거두고 시계 판은 안 거둔다(자리를 뜬 뒤에 창이 뜨면 놀란다). 손의 숨 표가 끊겼으면 창은 남기지 않고 대화로
  가시라고 말하고, 누른 지 `ASK_TAKE_S` 안의 누름만 맡는다
- **연 문서는 보고 글이 정한다** — 창의 저장소는 file: 창끼리 하나라, 손은 누른 창의 보고 글에 링크로 선 id(`brief_inline.approvals_in`)만 연다
- **결재 줄에는 누름 단추가 없다** — 결재하시면 결재함에서 저절로 빠지고, 다음 보고는 결재함을 다시 읽는다
- **id 의 꼴은 손사본이다** — `brief_inline.APPROVAL_ID` 는 결재 스킬 `iams.KEY` 와 같은 꼴이다(창의 손은 홀로 서야 해 못 싣는다). 꼴이 아닌 id 는 쓴
  그대로 글자로 서고 끝 줄 앞에서 경고한다

### 메일 한 장 — 자리 밖에서 보기

`window.py --sheet <보고 글> --slot <칸의 날과 시각>` 이 창과 같은 보고 글을 같은 꼴 읽기로 읽어 휴대폰 너비의 메일 한 장({subject, html,
text})을 표준 출력에 낸다(`render_mail.mail_sheet`) — 같은 사실을 두 자리에 쓰지 않는다. 쓰지도 보내지도 않는다 — 부르고 보내는 것은 스킬
mailbox-scan 의 판이다.

- 꾸밈은 줄마다의 style 속성에 든다 — 메일 프로그램이 `<style>` · 스크립트 · 바깥 글꼴을 거른다
- 누름 단추와 링크가 없다 — 근거 메일은 보고 글이 쓴 그 글(보낸 분 · 날짜 · 제목)로 서고, 맡길 일은 종류와 창의 줄과 같은 글로 서며 맡길
  일이 든 절에는 PC 의 보고 창에서 맡기시라는 한 줄(`MAIL_TASK_INTRO`)이 더 선다
- 제목은 그 칸이 든 날과 그 시각이고 끝의 「… 지음」은 지은 때다 — 저녁 칸의 보고가 자정 뒤에 지어져도 제목이 다음 날을 대지 않는다
- 빈 기록 절은 창처럼 빼고 나머지 절은 다 싣는다. 끝에 끄는 자리를 댄다

### 창 곁의 손

창 곁의 손(`presses.watch` — `ticks.py --watch` 로 뜬다)은 열린 보고 창 하나에 붙어 `STEP_S` 마다 누름을 거두고, 숨 표(`brief_const.HAND_KEY`)를
`brief_const.HAND_BEAT_S` 마다 적는다. 걸음마다 맡길 일을 먼저 돌보고(`Hand.tend` — 누른 지 몇 초 안에 맡아야 한다) 그다음 누름 종류
표(`presses.KINDS` — 부탁 · 일정에 넣기 · 자리 밖에서 보기 · 보고 시각)의 차례대로 거둔다. 새 누름은 이 표의 줄 하나(열쇠 · 거둘 때인가 · 할 일 ·
돌려 적을 칸)와 할 일 함수 하나다 — 시계 판의 뒷받침도 같은 줄로 재고 같은 칸을 적는다.

- **오래 걸리는 부름 사이에도 산다** — 일정 손 · `unattended/` 입구의 명령 · VS Code 를 기다리는 동안에도 숨 표를 적고 새 맡길 일을 맡는다(`presses.wait_out`
  · `Hand.tend`). 돌보다 넘어지면 그 말을 남기고 다음 걸음에 기록을 다시 읽는다 — 기다리던 부름을 버려 두지 않는다
- **끝나는 때** — 열린 보고 창이 없어지면 끝나고, Edge 와 연달아 못 주고받아도 끝난다 — 맡긴 판이 도는 동안은 둘 다 기다린다. 둘째 손은
  잠금(`HAND_LOCK`)을 못 쥐고 바로 끝난다. 뜨고 끝난 까닭은 `HAND_LOG` 에 남는다
- **시계 판이 되살린다** — 시계 판이 누름을 거둘 때(`presses.round_once`) 손을 띄울 창이 열려 있는데 손이 없으면 다시 띄운다 — PC 를 다시 켜
  Edge 가 창을 되살린 아침에도 「바로」가 돌아온다
- **손이 없을 때 사람이 안다** — 창은 숨 표가 `HAND_BEAT_S` 의 세 배 넘게 없으면 손이 없다고 보고, 누름 직후의 말을 그것으로 고른다

### 정한 시각의 보고 — 시계 한 판

정한 시각에 사람 없이 보고를 띄우는 일은 `unattended/` 의 시계가 든다. 작업 스케줄러가 시계의 주기(`CLOCK_EVERY_MIN`)마다 시계 작업(`\mail-secretary\daily-brief`)을
부르고, 작업이 `clock.py tick` 한 판을 돈다. 메일함 스캔은 작업 스케줄러에 걸지 않는다 — 스캔은 메일함만 읽고 정한 시각을 모르며, 시계가 보고
시각에 스캔에 한 판을 청한다. 시계 판은 보고 시각의 칸 밖에서는 메일함에 안 닿아, 주기는 메일 서버의 부담이 아니라 보고가 얼마나 늦게 서나 ·
보고 창의 누름을 얼마나 늦게 거두나다. 판은 앞 판이 도는 동안 온 주기를 건너뛰고(`IgnoreNew`) 판 안에서 OS 잠금(`oslock.py`)을 한 번 더 쥔다.
시작 때는 주기의 절반 뒤로, 로그온 뒤 첫 판은 바탕(`SCAN_LOGON_DELAY_MIN`)에 주기의 절반을 더해 건다 — 옛 판이 건 스캔 작업이 아직 안 거둬진 PC 에서
두 작업이 같은 분에 깨지 않게다. 청한 판이 대화의 판과 겹치는 날은 청하는 쪽이 늘 `--wait` 를 주어 앞 판이 끝나기를 시한 안에서 기다린 뒤 돌게 한다.

보고 시각이 없어도 대화에서 건 시계(`clock.py register`)는 판마다 돈다 — 창에서 누른 「일정에 넣기」를 창 곁의 손이 못 받았을 때 거두는 뒷받침이 보고
시각과 상관없이 판마다 돌기 때문이다. 보고 시각이 없는 판은 창의 고름 · 누름만 보고 끝난다 — Edge 의 포트가 안 받으면 프로세스 하나 띄우고 바로 끝난다.

한 판은 이 차례로 엮는다 — 자리 밖에서 보기의 메일을 먼저 보내 그 끝이 이 판에 띄우는 보고의 부탁 글에 실리게 하고, 창에서 고르신 것을 받고,
띄울 때면 띄우고, 「일정에 넣기」 누름은 몇 분이 들 수 있어 맨 뒤에 거둔다.

```
tick ─▶ OS 잠금 ─▶ away_mail.mail_step ─▶ window_choices(창 이음 → brief_window · away_mail) ─▶ brief_step: brief_day(지금 칸)
   → brief_state(칸의 상태 · 띄울 때인가 · 입구를 부를 판인가) → session_login.look · sign_in → 스캔에 한 판을 청한다(scan_door) → claude_launch.launch
   ─▶ window_link.window_presses
```

「로그인 → 읽기 → 띄우기」가 한 판이다. 시계는 스캔의 속을 모르고 스캔은 보고를 모른다 — 시계는 `scan.py run --now --wait` 로 한 판을 청하고
`scan.py status --json` 의 마지막 판이 청한 뒤에 시작했는지 · 세션 답이 `live` 인지로 돈 것을 읽는다(약속 절 「스캔의 두 문」). 보고 시각이 아닌 판에는
스캔을 청하지 않는다.

#### 시각표와 칸 · 언제 띄우나

**시각표와 칸** — 사용자가 정한 보고 시각(하나 이상 · `daily-brief-schedule.json` 의 `times`)마다 그 시각부터 끝까지가 그 시각의 칸이다. 끝은 다음
시각 · 그 시각에서 기다림의 상한(`BRIEF_WAIT_MIN`) 분 뒤 · 그날 자정 가운데 이른 것이다 — 사용자에게 시각마다 마감을 따로 묻지 않고 시각표에서
끌어낸다. 상한을 두는 까닭은 아침 보고가 오후에 서지 않고 사내 인증을 하루 내내 두드리지 않게다. 칸의 길이가 `BRIEF_ROOM_MIN` 분이 안 되는
시각이 있으면 거는 명령이 거절한다 — 시계는 제 주기(`CLOCK_EVERY_MIN`)마다 깨는데 그 틈이 모자란 칸에는 판이 안 돌아 날마다
조용히 안 뜬다. 시각 하나를 쓰던 옛 설정(꼴 1 · `at`)과 옛 그날 칸(`tries` · `launched`)은 다시 안 걸어도 첫 시각의 것으로 읽는다.

**언제 띄우나** — 판 안에서 다 서면 한 번 살펴본다: 보고를 걸었다 · 서울 시각이 어느 칸 안이다 · 그 칸의 보고 글이 아직 없다(덮는 첫때 — 앞 칸의
끝, 첫 칸은 0시 — 부터 그 칸의 끝 전에 `brief_const.FILE_NAME` 꼴의 이름에 때가 든 글 · 대화에서 지었어도 있다. 칸이 띄운 보고가 남긴 글은 그 칸의
것이다 — 칸 끝 무렵 띄운 보고는 글을 칸이 끝난 뒤에 써, 그 글로 다음 칸이 안 띄우면 안 된다) · 그 칸에서 아직 안 띄웠다 · 시계가 띄운 보고가 도는
중이 아니다(띄운 기록 `daily-brief-launch.json` 의 띄운 때 · 프로세스 번호로 `run_end` 가 가른다 — 아래 「끝났나」). 살펴보기는 사내 세션이 살아 있나다
— 살아 있으면 띄우고 그 칸은 끝이고, 없으면 그 때를 적고 다음 판에 다시 본다. 수로 끊지 않고 칸의 끝으로 끊는다 — 사람은 어느 때에든 로그인하고, 그
뒤 첫 판이 띄워야 그 보고가 선다. 칸이 끝나면 그 시각은 그날 건너뛰고 `status` 가 시각마다 살펴본 때와 다음 걸음을 말한다. 그날 칸의 기록은 시각마다
따로 선다 — 시각표를 그날 바꿔도 띄운 시각은 또 안 뜬다. 그날은 서울 날짜로 새로 보고, 지난날 보고 없이 지나간 시각은 새 날의 `before` 에 한 줄씩
남아 `status` 와 그날 첫 보고의 부탁 글이 말한다. 띄운 보고의 부탁 글은 그날 마지막으로 보고 글을 남긴 칸 뒤에 건너뛴 시각을 싣는다(지난날의 줄은 그날
아직 보고가 없을 때만). 띄웠는데 글 없이 끝난 칸(아래 「끝났나」로 끝났는데 그 칸에 보고 글이 하나도 없다 — 자리 밖에서 보기가 보낼 글을 고르는 셈과
같다)과 못 띄운 칸도 보고 없이 지나간 시각이다 — 그렇다는 줄로 같은 자리에 선다. 그 칸을 다시 띄우지는 않는다(그날 그 시각은 한 번 띄운다).

- **걸기 전에 이미 지난 칸은 건너뛴 것이 아니다** — 시각표를 건 때(`set`)보다 앞에 끝난 칸은 그날 「이미 지난 시각이라 내일부터 뜬다」로 말하고,
  건너뛴 보고의 줄(`status` · 다음 보고의 부탁 글)에 안 넣는다
- **`status` 는 약속하지 않는 것을 약속하지 않는다** — 시계 작업이 작업 스케줄러에 없으면 맨 위에 그렇다고 대고, 오지 않을 시각마다 「안 뜬다」로
  말한다. 앞 칸의 끝 뒤 · 이 칸의 시작 전에 대화에서 지은 보고 글이 이 칸을 대신하면 「○○:○○에 지은 보고 글이 이 시각의 보고를 대신한다 — 이
  시각에는 안 띄운다」로 말한다(방금 청하신 보고를 거듭 짓지 않는다)

#### 사내 세션과 스스로 로그인

- **보고 시각을 건 것이 곧 그 시각의 스스로 로그인이다 — 그날 첫 시각에 한 번, 뒤 시각은 세션이 끊겨 있을 때 그 칸에서 한 번** — 따로 켜는
  칸은 없다(시각표 파일의 옛 `login` 칸은 안 읽고, 시각을 다시 걸면 걷힌다). 보고 시각을 안 건 PC 는 로그인하지 않는다 — 시계 판은 시각표가 없으면
  창의 고름 · 누름만 본다. 부를 판인가는 한 자리(`brief_state.login_due`)가 가른다. 첫 시각의 칸에서 띄우기 앞의 첫 판이 형제 스킬 ep-login 의 입구를
  사람 없는 꼴(`LOGIN_ARGS`)로 한 번 부르고, 서면 그 판에 띄운다. 첫 시각은 세션이 살았어도 부른다 — 포트 창 세션은 PC 를 새로 켠 뒤에도 살아 있을
  수 있고, 평소 Edge 로그인(로그온마다 한 번 · DRM 문서가 기대는 것)은 입구가 든다. 뒤 시각의 칸은 세션이 끊겨 있을 때만 같은 꼴로 한 번 부른다 — 낮에
  사람이 평소 Edge 에서 다시 로그인한 날에도 그 시각의 보고가 빠지지 않는다. 세션이 살아 있으면 안 부른다(창이 안 뜬다)
- **로그인이 서면 스캔에 한 판을 청해 산 세션에서 메일함을 읽은 뒤 띄운다 — 로그인 → 읽기 → 띄우기가 한 판이다** — 시계가 세션을 보고 입구를 부른
  다음 스캔에 `run --now --wait` 로 새 판을 청하고(전체를 볼지 새 메일만 볼지는 스캔이 제 때로 고른다), 그 판이 청한 뒤에 시작했고 세션 답이 `live` 일 때만 띄운다. 보고는 사람이 정한 그 시각의 판에
  서고, 그 판이 칸의 마지막 판이어도 빠지지 않는다. 첫 시각도 뒤 시각도 같다 — 첫 시각의 칸에서 세션이 살아 있던 아침도 같은 길로 한 판을 청해 읽은 뒤
  띄운다. 입구를 부르는 자리는 하나(`self_login`)이고, 스캔을 청하는 것은 입구를 부르지 않는다. 청한 판이 세션 없음이면(사람이 그 사이 다른 자리에서
  로그인했다) 그 판은 안 띄우고, 그 칸에서 입구를 다시 안 부르며, 그 칸의 뒤 판이 산 세션에서 읽으면 한 번 띄운다. 청한 판이 건너뛰었으면(스캔이
  이미 한 판을 돌고 있었고 시한 안에 안 끝났다) 그 칸의 다음 시계 판이 다시 청한다 — 로그인은 칸마다 한 번이라 다시 안 한다. 정한 시각보다 늦게
  서는 갈래는 이 둘뿐이라 `status` 가 그 까닭을 댄다. 청한 판이 못 돌았으면 `[보고 예약 — … 메일함 스캔 한 판을 못 받아 못 띄웠다(…)]` 한 줄이
  그 까닭을 대고 칸의 끝까지 다음 확인에 다시 청한다. 입구의 끝은 그 한 번의 자리에 적는다 — 그날의 한 번은 그날 장부의 `login`, 뒤 시각의 한 번은 그
  칸의 `login` — 적힌 자리는 다시 안 부른다. 입력 없이 넘는 통합 인증으로만 선다 — 아이디 · 비밀번호를 어디에도 두지 않고, 사람이 쳐야 하는
  자리(SSO 가 안 서는 로그온 · 통합 인증이 안 선 화면)에서는 입구가 창을 띄우거나 기다리지 않고 끝난다. 못 세운 칸은 다시 안 부르고 기다리며, `status` 가 안 선
  까닭과 — 칸이 끝나면 — 건너뛴 까닭을 댄다. 손이 세션을 못 살펴본 판(손 오류)은 입구를 안 부르고 그 한 번도 안 쓴다. 띄운 ep-login 창은
  그대로 둔다 — 보고 창이 그 Edge 의 새 탭으로 뜬다
- **보고 시각 사이의 판은 로그인하지 않는다** — 칸 밖의 판과 이미 띄운 칸의 판은 세션이 끊겨 있어도 입구를 안 부른다. 로그인하는 순간
  사람의 평소 Edge 에서 사내 메일 · 일정 창이 닫히고 EP 포털이 죽어(거기서 앱을 새로 못 띄운다), 판마다 되풀이하면 사람이 다시 로그인할
  때마다 다음 판이 그것을 도로 끊는다. 그 값은 보고 시각에만 치르고, 사람에게는 보고 시각을 걸 때 늘(거는 줄 · 스킬 글 · 첫 확인
  글 · 보고 창의 「보고 맞추기」)과 그 보고의 창이 말한다 — 보고 시각을 거는 것이 그 값을 받아들이는 것이다. 띄운 ep-login 창은 디버깅 포트를
  연 Edge 라 그 PC 의 다른 앱과 부딪힐 수 있다 — 로그인을 원치 않는 사람의 길은 보고 시각을 내리는 것이다
- **세션 없이 스스로 로그인한 때는 보고 창이 읽는 자리에 남긴다** — 그 로그인이 선 판이 시각표 파일의 `signed` 칸에 로그인한 때(`at`)와 그
  로그인으로 띄운 보고가 글을 남길 수 있는 끝(`until` — 띄운 때에서 `BRIEF_LOCK_STALE_S`)을 띄우기 전에 적는다(`brief_schedule.note_signed`). 적는
  자리는 띄우는 판 하나다(`clock_round.note_launch` — 그 칸의 로그인을 `brief_state.slot_login` 이 고르고, 첫 시각은 끊긴 세션 앞의 부름(`lost`)일
  때만 적는다). 이 스킬의 창이 그 사이에 지은 보고의 머리에 「사내 로그인을 새로 했다 · 이 보고가 끝나고 돌려준다」 한 줄을 세운다(위 「스스로 로그인해 지은 보고의
  한 줄」) — 모델이 옮겨 적지 않는다. 살아 있던 세션 앞의 부름(그날 첫 시각)은 로그인을 새로 했는지 몰라 안 적는다. 못 적으면 그 줄만 안 선다
- **세션 보기는 로그인하지 않는다** — 칸 안에서 세션을 보는 것은 메일 손의 `session` 한 번이다. 그 명령은 있는 세션 파일로 묻고, 서버가 거절하면
  사람의 Edge 에 이미 선 세션을 받아 올 뿐 로그인 화면 · 창 · 탭을 열지 않는다(손 `mail.py` 머리말 「세션」 · 스킬 ep-login 의 `edge_session.js`
  머리말). 그 부름은 그 칸의 마지막 살펴보기에서 `BRIEF_TRY_GAP_MIN` 분이 지난 판만 한다 — 작업이 더 자주 깨워도 SSO 를 촘촘히 안 두드리고, 칸
  밖에서는 안 부른다. 청한 판이 손에서 받은 답(`status --json` 의 `last_run.session`)은 틈과 상관없이 쓴다 — 세션 파일이 끊긴 뒤 새로 쓰여(대화의
  EP 로그인 · 다른 사내 앱 스킬이 새로 받음) 스캔이 바로 돈 판이 살아 있음을 보면 그 판에 띄운다

#### 사람의 로그인을 돌려준다

시계가 끊긴 세션 위에서 스스로 로그인하면 사람의 평소 Edge 의 EP 포털이 죽어 ERP · MES 를 새로 못 띄운다. 그 로그인은 보고 하나를 짓고 보고
창의 단추가 몇 번 쓰려고 빌린 것이라, 다 쓰면 형제 스킬 ep-login 입구의 돌려주는 문(`--give-back --unattended`)으로 사람에게 돌려준다 — 평소 Edge 에
로그인을 다시 열고 포트 창의 EP 포털 · 로그인 화면 · 메일 목록 탭과 평소 Edge 의 끊긴 EP 탭을 닫는다(끝 줄 · 종료 값은 그 입구의
머리말 「프로그램이 부르는 문」). 빌리고 돌려주는 자리는 `loan.py` 하나이고 OS 잠금(`LOAN_LOCK_FILE`) 아래에서 한다 — 시계 판 · 창 곁의 손 ·
맡긴 일의 지킴이가 함께 불러도 입구는 한 번이다.

- **보고가 끝나고 `GIVE_BACK_AFTER_MIN` 분 뒤 처음 도는 판에 한 번** — 돌려줄 로그인은 그날 장부의 보고 앞 로그인 가운데 시계가 끊긴 세션 위에서
  세운 것이다(첫 시각은 `lost` 인 그날의 한 번 · 뒤 시각은 칸의 한 번 — `loan.loans_of`). 때는 그 칸이 띄운 보고가 끝난 때(`brief_reports.launched_end`
  — 프로세스가 사는 동안은 기다리고, 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다)에서 잰다 — 보고가 아직 돌면 정한 시간이 아니라 그 끝을 기다린다.
  그 틈은 사용자가 정한 것이고 보고 창의 「일정에 넣기」 · 「결재 창 열기」 · 「맡기기」가 그 로그인을 쓰는 동안이다. 시계의 주기(`CLOCK_EVERY_MIN`)를
  기다리면 그 틈에 주기만큼 더 늦으니, 돌려줄 때가 다 선 판은 그 때(`WAKE_SLACK_S` 뒤)에 시계 판 한 번을 부르는 한 번만의 작업
  (`clock_task.GIVE_BACK_TASK_NAME` — 돌고 나면 작업 스케줄러가 지운다)을 걸거나 그 때로 고친다(`loan.wake`). 그 판을 놓쳐도 시계의 다음 판이 한다.
  판의 맨 끝(누름 거두기 뒤)에서 한다 — 남은 누름이 그 세션에서 먼저 든다
- **한 번 돌려준 로그인은 다시 안 돌려준다** — 돌려준 끝을 빌림 파일(`LOAN_FILE` 의 `given`)과 그 로그인 기록(`given`)에 함께 적는다. 돌려주면 이
  세션이 끊겨 뒤 시각은 끊긴 세션에서 다시 로그인하고(`login_due` 그대로), 그 로그인도 그 보고 뒤 10분에 돌려준다. 한 로그인이라도 아직 그 틈
  안이거나 그 세션을 쓰는 일(시계가 띄운 보고 · 빌린 일)이 있으면 기다린다 — 한 번 돌려주면 그 세션을 다 끊는다
- **살아 있던 세션 앞의 부름은 안 돌려준다** — 첫 시각은 세션이 살아도 입구를 부르지만, 그 세션은 사람이 대화에서 세운 것일 수 있다(시계가 로그인을
  새로 했는지 모른다 — `note_launch` 가 보고 창의 한 줄을 안 세우는 것과 같은 자). 대화에서 세운 로그인은 대화가 일을 마친 뒤 사람에게 묻고 돌려준다
  (회사 스킬 머리 줄 · 스킬 ep-login 「사람의 로그인을 돌려준다」)
- **SSO 가 안 서는 로그온은 그날 다시 안 부른다** — 그 문의 4 는 아무것도 안 열고 안 닫았다는 뜻이다(칠 사람이 없다). 끝을 적고 그날의 나머지
  로그인에도 같은 끝을 달며, `status` 가 그렇다는 것과 대화의 「EP 돌려줘」를 댄다
- **돌려준 뒤 누른 단추는 잠깐 빌린다** — 「일정에 넣기」가 세션 없음(`records.SESSION`)을, 결재 창 열기가 세션 없음(`APPR_SESSION`)을 내면 창 곁의
  손(`presses.Borrow`)이 시계의 `clock.py lend` 로 한 번 빌리고 그 일을 다시 한 뒤 `release` 로 놓는다. 맡긴 일은 지킴이(`handed.watch`)가 claude 를
  띄우기 전에 `loan.lend` 로 세션을 쓴다고 적고(끊겼으면 빌리고) 끝나면 놓는다 — 산 세션에서 맡긴 판도 적어, 시계가 그 판 도중에 돌려주지 않는다.
  빌리는 것은 오늘 이 PC 가 돌려준 뒤일 때뿐이다 — 돌려준 적이 없는데 끊겼으면 사람이 다른 자리에서 로그인했거나 대화의 세션이 끊긴 것이라 전처럼
  대화의 로그인을 청한다. 빌린 로그인이 섰는데 또 끊기면 다시 안 빌리고(사람이 다른 자리에서 로그인했다), 빌린 로그인 위에서도 세션 없음이면 그 일에는
  그날 다시 안 빌린다(`futile` — 판마다 로그인과 돌려주기를 되풀이하지 않는다)
- **한 걸음에 로그인 하나 · 끝나면 곧 돌려준다** — 한 걸음의 「일정에 넣기」 누름 여럿은 로그인 하나를 함께 쓰고 그 걸음 끝에 놓는다. 쓰는 일이 더
  없으면 놓는 손이 그 자리에서 돌려준다(못 하면 다음 시계 판). 일마다 쓸 끝(`until` — 그 일의 천장)을 적어, 놓는다고 하기 전에 죽은 손이 영영
  붙들지 않는다
- **결재 창은 `GIVE_BACK_AFTER_MIN` 분 더 둔다** — 결재 창은 그 세션이 사는 Edge 에 떠 사람이 그 창에서 결재한다. 띄운 직후에 돌려주면 그 창이 죽는다. 그래서 띄운
  결재 창은(빌렸든 산 세션이든) 놓을 때 `GIVE_BACK_AFTER_MIN` 분 더 쓰는 것으로 적고, 그 뒤 시계 판이 돌려준다
- **`status` 가 말한다** — 돌려준 끝마다 한 줄(때 · 닫은 EP 탭의 수 · 어느 로그인), 아직 안 돌려준 보고 앞 로그인은 언제 돌려주나, 단추가 빌려 쓰는 중인
  로그인(`loan.status_lines`)

#### 띄운 claude

- **띄운 claude 는 읽는 명령과 업무 파일의 쓰는 손만 연다** — 권한 방식 dontAsk(허용 목록 밖은 묻지 않고 막는다) · 기본 도구는
  `CLAUDE_TOOLS` 뿐(파일을 쓰는 도구가 없다) · MCP 없음. 열린 명령은 손의 읽는 명령(`MAIL_READS` · 주소록의 찾기 `DIRECTORY_READS` · `CALENDAR_READS` · `MEETING_READS`) · 스킬 mailbox-scan 의 읽는 명령(`reader.py`) ·
  보고 창(사용자 폴더에 짓고 띄워 둔다) · 창의 표시를 거두는 손(뒤 인자 없이) · 업무 파악 스킬(`WORK_SKILL`)의 쓰는 손(`WORK_WRITER` — 업무 파일 하나만 쓰고 앞 판의 절이 빠진
  글은 안 쓴다)이고, 그 밖의 명령 · EP 로그인 · 문서함 스킬은 열지 않는다. 부탁 글은 창의 표시를 먼저 거두고, 업무 파악을 한 뒤, 보고를 지으라고 한다. 사용자 설정의 allow 가
  함께 실려도 바꾸는 · 내보내는 명령은 `BRIEF_DENY` 가 막는다. 일정 손의 미리 보기(`preview`)는 일정을 안 바꾸는 읽기라 연다 — 보고가 「일정에
  없는 약속」 카드에 그 판의 값과 열쇠를 싣는다. 넣기(`add`) · 고치기 · 지우기와 회의실 손의 넣기 · 고치기 · 취소 · 설정은 막힌 채다 — 일정에
  넣는 것은 사람이 카드를 누른 뒤 코드가 그 열쇠로만 한다(위 「일정에 넣기」)
- **열린 명령의 인자 칸(끝의 「 *」)에 무엇이 와도 경계가 선다** — 보고 창 손은 `--dir` 를 두 번 안 받고(사용자 폴더 밖에 못 쓴다), 손의
  읽는 명령이 파일을 쓰는 깃발은 `BRIEF_DENY` 가 막는다. 경로는 Git Bash 와 파이썬이 함께 읽는 「C:/…」 꼴로 따옴표에 싼다
- **막힘 하나가 판 전체를 멈추지 않게 부탁 글이 두 가지를 댄다** — Claude Code 는 한 부름의 명령을 `;` · `&&` · `|` 로 갈라 하나하나를 규칙에
  대고, 어느 규칙에도 안 맞고 읽기 전용으로도 안 읽히는 조각이 하나라도 있으면 그 부름을 통째로 막는다. `echo "EXIT=$?"` 처럼 변수를 펴는
  조각은 읽기 전용으로 안 읽힌다. 막힘의 답은 「Permission to use Bash has been denied …」라 모델이 Bash 가 꺼졌다고 읽고 거기서 그칠 수
  있다 — 첫 Bash 부름이 그렇게 막히면 보고 없이 끝난다. 그래서 부탁 글이 열린 꼴 곁에 둘을 적는다: 종료 값은 도구의 결과가 대니 덧붙이지
  않는다 · 그 답은 그 명령 글 하나가 꼴과 달랐다는 뜻이니 덧붙인 것을 걷고 다시 부른다. 열린 꼴을 늘려 덧붙임을 받지 않는다 — 열린 명령은
  하는 일로 정하고, 같은 일을 다르게 쓴 글을 따라 늘리지 않는다
- **띄우고 기다리지 않는다** — 창 없는 콘솔 · 새 프로세스 무리로 띄우고 판은 바로 끝난다. 작업 스케줄러의 실행은 job 안이라 그 job 을
  벗어나는 띄우기는 거절된다 — 그대로 띄워도 작업의 판이 끝난 뒤 살고, 작업은 그 판이 끝나면 「준비」로 돌아가 다음 주기를 막지 않는다.
  출력은 사용자 폴더에만 남는다
- **띄우는 꼴** — `--settings`(권한 파일 `daily-brief-launch-settings.json`) · `--permission-mode dontAsk` · `--tools` · `--strict-mcp-config` ·
  `--no-session-persistence` · 스킬 폴더마다 `--add-dir`. 작업 자리는 사용자 폴더이고, 부탁 글은 `daily-brief-launch-prompt.txt` 를 표준 입력으로 준다.
  환경은 겹친 세션의 표지(`NESTED_ENV`)를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다(`child_env`)
- **끝났나** — 한 자리(`brief_reports.run_end`)가 가른다: 다음 칸이 다시 띄웠거나(출력 파일 `daily-brief-launch.log` 은 띄울 때마다 새로 쓴다) ·
  띄운 프로세스가 없거나 · 띄운 때에서 `BRIEF_LOCK_STALE_S` 가 지났으면 그 보고는 끝났다. 프로세스 번호가 없는 옛 기록 · 못 읽은 기록만 출력
  파일에 글이 섰나로 본다 — `claude -p` 는 다 끝난 뒤에 답을 낸다. 띄울 때 띄운 기록(`daily-brief-launch.json`)과 칸의 띄운 기록에 같은 띄운 때 · 같은
  프로세스 번호를 적는다 — 띄운 기록은 그날 장부가 못 보는 띄움(앞날 늦게 · 장부를 못 적은 판)도 덮는 증거이고, 끝의 규칙은 따로 안 든다. 그래서
  `status` 의 「짓는 중 · 안 섰다」(`launch_outcome`) · 칸의 보고 글 범위(`launched_span` — 띄운 때부터 끝난 때까지) · 앞 보고가 도나(`lock_held`
  — 새 보고를 띄워도 되나) · 부탁 글의 건너뛴 칸 · 자리 밖에서 보기의 보낼 글이 다 그 끝을 읽는다. 띄운 기록은 지우지 않는다

#### 보고 창에서 고르신 것을 받는다

시각표와 「자리 밖에서 보기」의 주인은 시계(`unattended/`)이고 보고 창은 같은 스킬의 `scripts/` 가 짓는다. 창 곁의 손과 시계 판, 두 길이 같은
자(`take_window_times` · `apply_away`)를 부른다. 시계에서 창의 손을 부르는 자리는 `window_link.py` 하나다.

- **보고 창에서 고르신 시각은 창 곁의 손이 바로 걸고, 시계 판이 뒷받침한다** — 창의 「보고 맞추기」가 고른 시각은 그 창(`file://` 페이지)의
  localStorage 에만 남는다. 창 곁의 손이 살아 있으면 그 손이 고름을 거둬 `clock.py window-times … --chosen-at` 으로 곧 건다 — 시계 판이 창에서 받을
  때와 같은 한 자리(`take_window_times`)다. 시계 판도 판마다 받는다 — 손이 살았나는 안 본다(받은 고름은 시각표 파일의 `picked` 로 한 번만 건다): 보고가
  걸려 있고 로그인 Edge 의 디버깅 포트가 받으면(안 받으면 손을 안 띄운다) 판마다 창의 문(`window_door.read_choices` — 같은 스킬의 함수)으로 이 PC 의 디버깅 포트로 열린
  보고 창에서 읽고(열린 창이 없으면 탭을 안 연다), 거는 명령과 같은 자(`times_given` · 틈의 셈)로 재 시각표에 건 뒤 받았나 · 까닭을 `--times-done` 으로
  그 창에 돌려 적는다. 받는 것은 시각과 「자리 밖에서 보기」뿐이다 — 보고를 걸고 내리기 · 스스로 로그인 · 띄울 claude 는 대화에서만 바뀐다.
  **나중의 말씀이 이긴다** — 창에서 고른 때가 시각표를 건 때(`daily-brief-schedule.json` 의 `set`)보다 앞서거나 같으면(그 사이 대화에서 바꾸셨다 ·
  고른 때를 못 읽은 것도) 안 걸고 그렇다고 적는다. 판마다 지금 걸린 시각표와 건 때 · 본 때를 그 창에 적는다(`state.state_of` · 손이 파일에서 끌어낸다).
  창의 고름은 보던 시각에서 더하고 빼신 것으로 지금 걸린 시각표 위에 얹는다(`apply_window`) — 창이 보여 드리지 않은 시각은 안 뺀다. 틈을 모자라게 하는
  더하신 시각은 하나씩(붙은 둘이 다 새것이면 늦은 쪽) 빼고 나머지를 걸며(모자란 틈이 더하신 시각 탓이 아니면 빼신 것까지 아무것도 안 건다), 걸지 않은
  시각을 다 까닭과 함께 · 건 것을 사실대로 · 지금 걸린 시각을 댄다(거는 명령의 거절도 지금 걸린 것을 댄다). 시각표를 걸 때 규칙의 수(`room_min` ·
  `wait_min`)를 그 파일에 함께 적어, 창이 더하실 시각을 같은 수로 바로 잰다
- **보고 창의 「자리 밖에서 보기」도 같은 물음으로 받는다** — 시계 판이 시각을 읽는 그 창의 문 한 번(`read_choices`)이 고르신 켬 · 끔과 고른 때도
  내고, 시계 판은 대화의 명령과 같은 한 자리(`apply_away`)로 건 뒤 `--away-done` 으로 그 창에 돌려 적는다(`window_away`). 창 곁의 손이 살아 있으면 그
  손이 같은 일을 `clock.py away … --chosen-at` 으로 바로 하고, 시계 판도 판마다 받는다 — 같은 고름을 둘이 함께 봐도 고른 때가 같으면 이미 받은 것으로
  지나간다. 나중의 말씀이 이긴다 — 고른 때가 걸어 둔 고른 때(`away.chosen`)보다 앞이면 안 건다
- **보고 창의 「일정에 넣기」는 시계 판이 뒷받침한다** — 누름은 창 곁의 손(보고를 짓는 쪽이 창을 열 때 띄운다)이 바로 거둔다. 그 손이 없는 날(PC 를
  다시 켰다 · 손이 죽었다)에도 누름이 버려지지 않게 판마다 — 보고를 걸었든 안 걸었든 — 넣는 손을 `ticks.py --presses` 로 불러 열린 보고 창의 누름을
  같은 코드로 맺고 끝을 그 창에 적는다(`window_presses`). 판단이 없는 일이라 모델을 띄우지 않는다. 한 누름은 한 번만 — 창 곁의 손이 먼저 넣은 누름은 그
  손의 기록으로 지나간다(위 「일정에 넣기」). 사내 로그인이 끊겨 남은 누름은 판마다 다시 해 본다 — 창 곁의 손의 다시 해 보는 사이를 안 기다려, 세션이
  살아난 뒤의 첫 판이 넣는다. 그 손에 주는 시간은 `BRIEF_PRESSES_WITHIN_S` 이고 그 안에 못 끝낼 넣기는 다음 판에 둔다 — 넣기 도중에 끊으면 들었는지
  모르는 끝이 남는다. 손을 띄울 창(`hand_wanted`)이 열려 있는데 창 곁의 손이 없으면 그 넣는 손이 다시 띄운다
- **대화에서 바꾸면 열린 창에 바로 알린다** — `clock.py at` · `off` · `register --at` · 대화의 `away`(고른 때 없이)가 끝나면 디버깅 포트가 받을 때 창의
  알림(`state.sync`)을 함수로 불러 열린 보고 창에 지금 모습을 적는다(`tell_window`) — 창은 다음 시계 판을 기다리지 않는다. 걸 때 작업 스케줄러에 시계가
  없으면 끝 줄이 그렇다고 대고 거는 길을 댄다. 다음 보고를 기다리지 않는 까닭 — 아침에 더하신 13:00 은 13:00 전에 보고가 없어 그날 안 선다

#### 자리 밖에서 보기 — 보내기

켜 둔 PC 에서 사람 없이 띄운 보고가 남긴 보고 글을 칸마다 한 통 본인 메일로 보낸다(`away_mail.py`). 메일 한 장은 이 스킬의 창 손이 짓고(`window.py --sheet`,
위 「메일 한 장」), 보내는 것은 보내는 손 `away_sender.py` 다.

- **켜기는 본인 주소를 받는 것까지다** — 켤 때 형제 스킬 company-directory 의 「나」(`DIRECTORY_ME`)를 한 번 불러 그 사람 파일의 주소 하나를 시각표 파일의
  `away.address` 에 적는다. 보낼 때 그 주소를 받는 사람과 보내는 사람 둘 다로 쓴다 — 창 · 보고 글 · 모델이 주소를 줄 칸이 아예 없다(보내는 손은 받는
  사람 인자가 없고 그 파일에서만 읽는다). 주소를 못 받으면(사내 로그인이 끊겼다 · 주소록이 한 사람을 안 냈다) 켜지 않고 까닭을 그 자리에 돌려
  적는다. 고른 것이 곧 동의라 따로 묻지 않는다. 보고가 안 걸렸으면 켜지 않는다. 시각표를 다시 걸어도 `away` 는 그대로 실린다(`save`) — 보고를 내리면
  함께 내린다
- **칸마다 한 통, 두 번은 안 보낸다** — 시계 판의 맨 앞(`mail_step` — 그 끝이 그 판에 띄우는 보고의 부탁 글에 실리게)에서, 켠 PC 에서만, 켠 뒤에 띄운
  칸마다 그 보고가 끝나(위 「끝났나」) 남긴 보고 글 한 장 — 띄운 때부터 그 보고가 끝난 때까지 이름의 때가 든 글 가운데 마지막 — 을 `window.py --sheet`
  로 메일 한 장으로 지어 보내는 손으로 보낸다. 대화에서 지은 보고는 띄운 칸이 없어 안 보낸다. 열쇠는 칸의 시각이다(판의 차례 번호로 짓지 않는다 —
  죽었다 살아난 판이 같은 칸을 다시 돌면 번호가 새로 선다). 중계를 부르기 전에 「보내는 중」 표지(`daily-brief-away-sending.json` — 그날 · 칸의 시각)를
  굳히고(못 굳히면 그 판에는 안 보낸다), 끝을 받으면 칸의 기록(`slots.<시각>.mail`)에 그 끝을 적는다 — 표지를 그날 장부와 따로 두는 까닭은 판 도중에
  장부를 쓰면 그 판의 다른 기록보다 앞서 굳어, 판이 죽으면 그 기록이 영영 안 적히기 때문이다. 끝은: 보냈다 · 넘기기 전에 졌다(연결 · 이름 찾기 · 거절
  코드 · 설정 · 메일 한 장을 못 지었다 · 손이나 보내는 손을 못 띄웠다 — 그 칸이 끝날 때까지 판마다 다시 보내고, 칸이 끝난 뒤 처음 보내 본 것은 한
  번) · 넘기는 도중이나 뒤에 졌다(중계가 받았는지 모른다 — 다시 안 보낸다). 다음 판은 표지를 걷되 그 칸의 기록에 표지보다 늦은 끝이 없으면 앞 판이
  보내다 죽은 것이라 「보냈는지 모른다」로 맺고 다시 안 보낸다 — 두 통을 보내기보다 못 보낸 채 알린다. 넘겼나는 보내는 손이 가른다: 중계가 거절
  코드로 답했거나 글(DATA)을 보내기 전에 진 것만 안 간 것이다. 보내는 손의 시한(`AWAY_SEND_TIMEOUT_S`)을 넘기면 모른다로 맺는다. `status` 의 그 칸
  줄과 다음 보고의 부탁 글(「건너뛴 보고 · 못 간 메일」)이 까닭을 한 줄로 댄다 — 부탁 글은 그 끝을 적은 뒤 띄운 보고가 아직 없는 것만 싣는다. 한 판에
  한 통까지이고, 판이 시작한 뒤 `AWAY_LATEST_S` 를 넘겼으면(주소록 한 번도) 새로 시작하지 않고 다음 판에 둔다 — 시작한 일과 뒤의 누름 거두기가 판의
  OS 잠금 · 작업의 시한 안에 끝나야 한다(그 끝은 시계의 제 시한에서 셈한다). 날이 바뀐 첫 판은 지난날의 칸부터 맺고 새 날로 넘어가, 자정 무렵
  띄운 보고도 간다. 시각표에서 빠진 칸도 띄운 기록이 있으면 끝난 칸으로 맺는다
- **보내는 손만 형제 스킬의 코드를 싣는다** — 사내 중계로 보내는 것은 회사 메일 손 곁의 `mailer.py`(명령이 없는 라이브러리)다. 시계 판은 그것을
  싣지 않고 보내는 손 `away_sender.py` 를 프로세스로 띄워, 그 라이브러리가 바뀌거나 없어도 판은 안 깨지고 「못 보냈다」만 적는다. 판의 모델은 이
  길에 없다 — 띄운 claude 에는 보내는 명령이 하나도 없다(`BRIEF_DENY`)

#### 옮겨 받기 — 어제의 파일로 오늘을 산다

사용자 폴더의 파일은 그 파일을 쓰는 스킬이 든다. 정한 시각의 보고가 스캔 자리(`mailbox-scan/`)에 두던 파일은 사용자 폴더 바로 밑 `daily-brief-` 머리의
파일로 옮겨 앉았고(약속 절 「새 파일 이름」), 옛 꼴을 가진 PC 는 옛 파일을 읽어 새 이름으로 옮겨 받는다.

- **누가 · 언제** — `clock.py adopt`(설치 · 대화가 부른다)와 시계의 첫 판이 같은 함수 하나를 부른다. 새 파일이 없고 옛 파일이 있을 때만 옛 것을 읽어 새
  이름으로 바꿔 끼워 쓴다. 옛 파일은 지우지 않는다 — 옮겨 받는 손이 도중에 죽어도 다음 판이 다시 읽는다. 새 파일이 있으면 옛 것은 다시 안 본다 — 옮긴
  뒤 바꾼 시각을 옛 것이 덮지 않게. 스캔은 옛 칸을 다시 안 쓰고 안 지운다
- **`adopt` 는 시계만 보고 이 홈으로 겨눈다** — 메일함 스캔의 작업에는 기대지 않는다(스캔은 작업을 걸지 않고, 설치가 옛 판의 스캔 작업을
  거둔다). 옛 파일을 옮겨 받은 뒤 걸린 시계의 인자를 거는 틀(`TICK_ARGUMENTS`)로 되읽어 견준다 — 이 홈의 입구 · 손을 부르면 그대로, 그 꼴이 아니면(손으로
  고쳤다) 안 건드리고, 다른 홈의 입구나 다른 손을 부르면 켜짐을 지켜 시계의 주기(`CLOCK_EVERY_MIN`)로 이 홈의 입구 · 회사 메일 손으로 다시 건다 — 걸린 주기는 옛 스캔의 `--every` 를 베낀 값일 수 있고, 보고 뒤의 돌려주기가 그 주기에 기댄다. 시계가 없으면 보고
  시각표(방금 옮겨 받은 것도)가 있을 때만 시계의 주기로 새로 건다 — 사람이 보고를 고른 PC 다. 손은 이 홈의 형제 스킬 company-mail 것, 사용자 폴더는
  스캔의 `status --json --dry-run` 의 `home`, 시각 · claude 는 사용자 폴더의 시각표에서(다시 걸어도 그대로다) 받는다. 여러 번 불러도 같다
- **설치는 한 홈에서 부른다** — 업데이트 때 깐 홈 가운데 정해진 차례의 첫째 한 홈에서만 부른다. 홈마다 부르면 홈끼리 서로 다시 겨눈다. 스킬
  mailbox-scan 의 `scan.py adopt`(옛 스캔 작업 거두기)와 차례에 안 기댄다
- **그날 장부** — 옛 `state.json` 의 `brief` 칸을 읽기만 한다. 날이 바뀐 장부여도 그대로 옮긴다 — 지난날 건너뛴 시각의 한 줄은 새 장부를 열 때 선다
  (`brief_day.roll_day`). 그날 이미 띄운 칸은 다시 안 띄우고, 띄운 claude 가 아직 돌면 옛 잠금(`brief.lock` 의 프로세스 번호)을 옮겨 받아 「짓는 중」으로
  본다
- **옛 꼴의 옛 꼴** — 시각 하나의 시각표(꼴 1 · `at`)와 그 꼴의 그날 칸은 지금도 읽는다. 옮겨 받기는 꼴을 바꾸지 않고 옮기고, 읽는 법이 함께 있다
- **도는 맡긴 판은 옛 자리에 둔 채 읽는다** — 지킴이가 흐름 파일을 쥐고 있어 옮길 수 없다. 새 판은 새 자리(`daily-brief-handed/`)에 쓰고 `show` ·
  `list` 가 옛 자리도 읽는다
- **그날 장부는 시계 하나가 쓴다** — 시계가 OS 잠금 아래 혼자 써서 두 파일에 두 번 쓰는 걱정이 없다. 띄운 뒤 장부를 쓰기 전에 죽은 판의 다시 띄움은
  띄운 기록(그 프로세스가 사나)이 막는다(`brief_state.slot_state`)

### 맡긴 일의 실행 — `handed.py`

보고 창에서 사람이 골라 맡긴 일들(회의실 잡기 · 답장 써 두기 · Teams 회의 띄우기 · 찾아 정리 따위)을 작업 폴더에서 claude 한 번으로 차례로 하게
뒤에 띄우고, 도는 동안 일마다의 끝을 프로그램(창 곁의 손)이 읽는 기록으로 낸다. 부르는 쪽은 이 스킬의 창 곁의 손(`runs.py`)이다 — `scripts/` 가
`unattended/` 를 싣지 않고 입구 명령으로 부른다(위 「맡길 일」).

**맡기는 것은 대화에서 시키는 것과 같다** — 실행에는 무엇을 할지(일의 종류 · 사람이 누른 줄 · 그 카드의 근거)만 주고, 회사 스킬의 손과 손가락은
실행이 엮는다. 그래서 띄우는 꼴에 권한 깃발 · 도구 · 모델 · 허락 목록이 없다 — 사람의 설정이 그대로 실린다. 누름이 곧 끝까지 하라는 승인이라
실행은 그 줄을 다시 묻지 않고, 메일은 임시보관함에 두고 그 화면을, Teams 회의는 채운 예약 창을 띄우는 데까지 간다(보내기는 사람 몫). 줄대로
못 끝낼 일은 바꾸지 않고 그 일만 멈춰 여쭐 말을 남기고 다음 일로 간다. 실행이 받는 글은 스킬 뿌리의 `handed-run.md` 틀에 일들을 채운 것이다. 이 손은
일의 글을 읽어 무엇을 가르지 않는다 — 받은 것을 그대로 넘기고 돌아온 것을 그대로 적는다.

**일마다의 끝은 표지에서 읽는다** — claude 의 출력 흐름(`stream-json`)에는 일을 가르는 표가 없다. 그래서 글이 실행에게 하나만 청한다: 한 일을
마치면 다음 일을 시작하기 전에 그 결과 글의 첫 줄을 「[일 N · 됨 | 여쭐 것 | 못 함 | 확인 안 됨]」 으로 연다(`MARK`). 표지 뒤로 다음 부름 전까지
온 글이 그 일의 결과 글이다. 다 마친 뒤 여러 일을 묶는 글은 「[맺음]」 으로 열게 한다 — 실행은 끝에 묶는 요약을 곧잘 쓰고, 머리가 없으면 그
요약이 마지막 일의 카드에 붙는다. 다음 일로 넘어간다는 말도 「[넘어감]」 으로 여는 줄에 쓰게 한다(`NEXT_WORD`) — 실행은 결과 글 끝에 그 말을
곧잘 덧붙이고, 자리가 없으면 그 말이 카드에 선다. 두 머리 뒤의 글은 어느 카드에도 안 붙는다. 손은 결과 글의 문장을 걷지 않는다.

**결과는 구조로 받는다** — 결과에 든 값(방 · 때 · 참석 · 받는 분 · 메일)은 사람이 카드에서 이름표와 함께 읽는다. 그래서 글이 실행에게 표지 아래를
JSON 객체 하나(`said` 머리 아래 한 문장 · `facts` [이름표, 값] 짝 · `items` 메일 한 통에 하나 · `more` 짧은 덧말)로 쓰게 하고, 이름표는 부르는
쪽이 일마다 준다(`tasks[].labels`). 글은 누가 읽는지도 댄다 — 창 앞의 그분께 높임말로, 그분의 말로, 프로그램 안의 번호 · 도구 이름 · 꾸밈 없이.
꼴(`handed.result_of`)을 지키면 기록이 그 칸을 `tasks[].result` 로 내고, 못 지키면 null 이다 — 그때 결과는 온 글(`text`) 그대로 선다. 글을
고쳐 꼴을 맞추지 않는다 — 고친 값은 사람이 못 본 값이다. 표지가 없는 일은 기록이 이렇게 가른다 — 도는 중이면 첫째가 하는 중 · 나머지는 기다림. 끝났으면 첫째는 마지막 표지
뒤에 부름이 있었을 때 「확인 안 됨」(하다 멈췄다 — 바꾸는 부름이었는지 모른다), 없었으면 「못 함」이고 나머지는 「못 함」(차례대로 하니 시작
안 했다)이다. 표지를 하나도 안 단 판이 무엇이라도 불렀으면 다 「확인 안 됨」이다. 들었을 수 있는 일을 「못 함」으로 말하면 사람이 다시 맡겨
두 번 든다 — 모를 때는 「확인 안 됨」으로 기운다.

**지킴이** — `start` 는 기록을 곧 쓰고 지킴이(`handed.py watch`)를 떼어 띄운 뒤 기다리지 않는다(부르는 손은 막히면 안 된다). 지킴이는 제 몸을 윈도의
작업 묶음에 넣고(마지막 손잡이가 닫히면 묶음 안을 다 끝낸다), 사내 세션을 손의 `session` 으로 한 번 본 뒤(없으면 claude 를 안 띄우고 로그인으로
맺는다), claude 를 작업 폴더에서 세션을 남긴 채 띄워 출력을 줄마다 받은 때와 함께 흐름 파일에 덧붙인다. 지킴이가 어떻게든 죽으면 OS 가 claude
와 그 아래를 함께 끝낸다 — 기록이 「멈췄다」를 말하는데 뒤에서 일이 이어지는 판이 없다. 다 끝나 맺을 때는 그 깃발을 걷고 나간다 — 일이 처음
띄운 브라우저 창(Teams 예약 창 따위)이 지킴이와 함께 닫히지 않게. 실행이 결과 글만 쓰고 차례를 마치면 `claude -p` 는 거기서 끝나 남은 일을
못 한다 — 글이 그러지 말라고 해도 실행은 그렇게 맺을 수 있다. 그래서 claude 가 종료 0 으로 끝났는데 표지가 없는 일이 남았고 마지막 표지 뒤로 부름이
하나도 없으면(하다 만 일이 없다 — 이어도 두 번 들지 않는다) 사내 세션이 끊겼다고 나오지 않으면 같은 세션을 `--resume` 으로 이어 남은 일을 하게 한다
(`RESUME_MOST` 번까지 · 이은 실행의 출력도 같은 흐름 파일에 덧붙는다). 하다 만 일이 있으면 잇지 않고 그 일은 「확인 안 됨」으로 맺는다.
`CEILING_S`(이은 실행까지 합친 시간)를 넘기면 claude 와 그 아래를 끊고 「끊김」으로 맺는다. 표지 없이
남은 일이 있는 판은 맺기 전에 사내 세션을 한 번 더 본다 — 없으면 「로그인 끊김」이다(손이 종료 3 을 낸 뒤의 일들은 그래서 못 했다). 실행이 제
까닭으로 「못 함」을 단 일은 안 센다 — 그 판을 로그인 탓으로 말하지 않게.

**읽기는 쓰지 않는다** — `show` · `list` 는 기록 파일 · 맡긴 일 · 흐름 파일에서 지금 기록을 그때마다 짓는다. 끝이 안 적혔는데 지킴이가 없으면
(번호를 적었는데 그 프로세스가 없다 · 적기 전인데 `START_GRACE_S` 가 지났다 · 맡긴 지 `STALE_S` 가 지났다) 다시 읽어 그래도 없을 때 「죽음」으로
낸다 — 끝을 적고 막 나간 지킴이를 죽음으로 읽지 않는다. 기록을 쓰는 것은 `start` 와 그 판의 지킴이뿐이라 잠금이 없다.

**파일의 자리** — 기록은 사용자 폴더의 `daily-brief-handed/<판>/` 에(기록 `run.json` · 맡긴 일 `tasks.json` · 실행이 받은 글 `prompt.txt` · 흐름
`stream.jsonl` · claude 의 오류 출력), 실행이 쓰는 파일(메일 본문 따위)은 작업 폴더의 `handed/<판>/` 에 둔다 — 글이 그 자리를 실행에게
댄다. 회사 스킬의 글은 본문 파일을 「임시 폴더」에 두라고만 해, 자리를 안 대면 실행이 작업 폴더 곁에 폴더를 지어 쓴다. 세션은 Claude Code 가 작업
폴더의 프로젝트 자리에 남기고, 기록의 `session` 으로 VS Code 의 작업 폴더 창에서 그 대화를 잇는다. 끝난 지 `KEEP_DAYS` 가 지난 판은 다음 `start`
가 두 자리(새 자리와 옛 자리) 다 걷는다(Claude Code 가 세션을 두는 기본과 같은 날 — 넘으면 이을 대화가 없다).

## 여러 흐름에 걸쳐 지키는 것

- **글은 다 글자로 선다** — 보고 글은 메일에서 온 글을 품는다. 모든 글을 HTML 이스케이프하고, HTML 을 그대로 싣는 길이 없다. 창의 스크립트는
  틀 곁의 `report.js` 하나이고, CSP 의 `script-src` 는 지을 때마다 그 글에서 낸 sha256 하나만 연다(`render.page_script`) — 메일에서 온 글이
  `<script>` · on… 속성으로 서도 돌지 않는다. 스크립트는 글을 짓지 않고 단추의 상태 · 줄의 class · 제 말 · 받은 글을 글자로 옮긴 것만 바꾼다
- **링크는 메일 번호에서만** — `[글](mail:<번호 32자리>)` 의 번호와 메일함 주소로 `<메일함>/XML_Inbox/<번호>?OpenDocument` 를 짓는다(폴더에만
  든 메일에도 먹는 주소다). 글에 쓴 다른 주소 · 링크는 쓴 그대로 글자로 선다
- **글에 없는 것은 더하지 않는다** — 절 이름 · 절 수 · 호칭 · 이름 · 회사는 글이 준 것만 선다. 틀이 더하는 것은 창의 이름표 · 지은 때 ·
  스스로 로그인해 지은 보고의 한 줄 · 「보고 맞추기」와 단추 · 칸 · 막대 · 사람별에 딸린 정해진 말뿐이다 — 보고 글의 사실을 새로 짓지 않는다. 빈 기록 절(줄이 없거나 「없음」 한
  줄)은 창에 안 서고 보고 글에는 그대로 남는다
- **메일함에 닿지 않는다** — 링크를 짓기만 하고 그 주소를 부르지 않는다. 그 주소는 열면 메일을 읽음으로 바꾼다. 망에 닿는 것은 이 PC 의
  디버깅 포트(`EDGE_HOST`)뿐이다
- **없음과 못 읽음은 다른 답이다** — 사용자 폴더의 파일(넣은 누름 · 맡긴 일의 기록 · 맞춤 파일 · 시계의 시각표 · 누른 창의 보고 글)은
  `store.py` 한 자리로 읽는다: 없으면 빈 것, 있는데 못 읽으면 못 읽음(바꿔 끼우는 순간의 PermissionError 는 잠깐 기다려 다시 읽는다). 읽은 뒤
  쓰는 손은 못 읽음에서 멈추고 그렇다고 말한다 — 빈 것으로 읽고 쓰면 넘긴 판 · 넣은 일정 · 감추고 미룬 일을 잃는다. 바꿔 끼우는 쓰기는 쓰는
  손마다 제 임시 이름을 쓴다
- **창의 저장소에 적힌 값은 믿지 않는다** — 저장소는 file: 창끼리 하나라 다른 창 · 다른 날의 값이 섞인다. 누름은 열쇠 · 누른 때 · 누른 창의
  이름만 들고, 넣을 값 · 맡길 일의 줄 · 부탁의 보고 이름은 손이 누른 창의 보고 글(같은 이름의 .md)에서 읽는다
- **단추 · 칸은 처음엔 숨는다** — 창의 스크립트가 주소 꼬리 `?via=edge` 를 보고 꺼낸다. 꼬리가 없는 창(기본 브라우저 · 파일을 두 번 눌러 연
  창)은 표시가 다른 저장소에 남아 영영 안 돌아오니 단추 대신 그렇다는 한 줄을 보인다. 스크립트가 막히면 아무것도 안 바뀐다
- **창이 스스로 짓는 말은 적다** — 끝의 말은 그 일을 한 손이 그 창에 돌려 적는다. 창이 고르는 말은 누른 직후 · 손이 없을 때 · 지난 카드 ·
  거둘 수 없는 창뿐이고, 손과 연락이 끊긴 일의 끝은 짓지 않는다(「맡길 일」)
- **형제 스킬은 명령으로만 부른다** — 이 스킬은 다른 스킬의 코드를 싣지 않는다. 일정 손은 이 파이썬으로 정해 둔 스크립트를 띄워 부르고(`presses.run_calendar` — 명령줄은 프로세스 바탕의 `proc_base.python_argv` 가 짓는다),
  같은 스킬의 `unattended/` 입구도 정해 둔 명령줄 하나로만 띄운다(`presses.run_unattended` — `handed.py` · `clock.py` 의 정해 둔 하위 명령에 `--dir` 를 붙인다). 사용자 폴더의 시각표 · 그날 장부는
  이 스킬의 파일이라 읽기만 한다(`state.py`)

## 약속 — 다른 스킬과 창이 기대는 것

같은 사실을 두 자리에 손으로 적지 않는다 — 아래 「원본」이 그 사실을 들고, 기대는 쪽은 거기를 가리키거나 그 명령의 답을 받는다.

| 무엇 | 원본 | 기대는 쪽 |
|---|---|---|
| 보고 글의 꼴(절 · 줄 · 칸 · 끝의 두 절) | `lane.md` 「보고 글의 꼴」 — 읽는 코드는 `brief_text.py` 와 곁의 `brief_*.py` · `task_kinds.py` | 보고를 짓는 모델 · 창 · 창 곁의 손 · 메일 한 장 |
| 보고 글 · 창의 파일 이름(지은 때가 이름) | `brief_const.FILE_NAME` — 가장 늦은 보고 글과 지은 때는 `window.py --latest` 가 답한다 | company-work(오늘 보고 — `--latest` 를 묻는다) · mailbox-work(가장 늦은 보고 글 — 글이 `--latest` 를 가리킨다) · 이 스킬의 시계(칸마다의 보고 글을 이 원본으로 찾는다) |
| 창의 저장 열쇠 | 머리 값은 `brief_const`, 창의 스크립트는 지을 때 그 값을 받는다 · 맡길 일의 칸은 위 「맡길 일」의 표 | `report.js` · 창 곁의 손 · 거두는 손 |
| 입구 명령의 꼴 · 내는 것 · 종료 값 | `window.py` · `ticks.py` · `prefs.py` 머리말 | 이 스킬의 `SKILL.md` · `lane.md` |
| 사람 없는 실행의 입구(`clock.py` · `handed.py`)의 명령 · 끝 줄 · 종료 값 · 새 파일 이름 | 아래 「사람 없는 실행의 문」 | 이 스킬의 `SKILL.md` · `first-setup.md` · `lane.md` · 설치(`adopt`) · `presses.py` · `unattended_link.py` |
| 시계가 쓰는 창 이음 — 프로세스로 부르는 문(`window.py --sheet` · `ticks.py --times-done` · `--away-done` · `--presses`)과 함수로 부르는 문(`window_door.read_choices` · `state.sync`) | `ticks.py` · `window.py` · `window_door.py` 머리말 — `--presses` 끝 줄의 머리는 `brief_const.ROUND_HEAD`, 알린 말은 `state.SYNCED` | 이 스킬 `unattended/` 의 `window_link.py`(프로세스로 부르는 한 자리) · `clock_round.py`(창의 문을 함수로 부른다) |
| 사람 없는 보고에 열린 명령의 꼴 | 이 스킬 `unattended/` 의 `claude_launch.commands` · 띄울 때의 부탁 글 | 이 스킬의 `lane.md` 「사람 없는 예약 실행」 |
| 맡긴 일의 명령 · 입력 · 기록 | 아래 「사람 없는 실행의 문」의 `handed.py` 표와 「맡긴 일의 파일과 기록」 | `runs.py` |
| 보고 시각표 · 규칙의 수 · 「자리 밖에서 보기」 · 세션 없이 스스로 로그인한 보고의 범위(`signed`) | 이 스킬 `unattended/`(시각표 파일 `daily-brief-schedule.json` 과 `clock.py` 명령) | `state.py`(읽기만) · 창 |
| 창 · 손이 사람에게 하는 말 | `report.js` · `render.py` 의 이름 붙은 글 · `presses.WORDS` · `asks.WORDS` · `runs.CANNOT` · `window_words.py` · `window_door.py` · `report_reads.py` · `ticks.py` · `prefs.py` 의 이름 붙은 글 | 사람 |

### 사람 없는 실행의 문 — `unattended/` (원본)

정한 시각의 보고(시계)와 맡긴 일의 실행은 `scripts/`(메일에서 온 글을 품은 창의 울타리)가 아니라 `unattended/` 에 산다. 입구는 둘 —
`unattended/clock.py` · `unattended/handed.py`. 둘 다 `python -X utf8 -I <스킬>/unattended/<입구> <명령> …` 으로 부르고, 입구는 싣는 것이 아니라
부르는 것이다(어느 모듈도 입구를 싣지 않는다). `scripts/clock.py`(때 짓기)와 이름이 같다 — 입구는 늘 `__main__` 이고, 안의 모듈이 싣는 `clock` 은 `scripts/` 의
것이라 입구가 `sys.path` 에 `scripts/` 를 `unattended/` 보다 **앞에** 둔다. 스캔의 두 문과 아래 파일 이름도 이 표가 원본이다.

`unattended/task_base.py`(작업 스케줄러를 부르는 몸 · 작업 정의의 틀 · 간격 읽기 · 로그온 뒤 첫 판의 바탕) · `scripts/proc_base.py`(곁의 파이썬 손을 창 없이 · UTF-8 로
띄우는 몸 — 창의 손도 쓰므로 `scripts/` 에 서고 `unattended/` 는 그것을 싣는다) · `unattended/hand_facts.py`(회사 메일 손의 자리 · 종료 값 · 시한 · 사내 세션의 답 낱말 · 다음 걸음)는 스킬 mailbox-scan 의 `scripts/` 에 선 같은 이름의 파일을 바이트째 베낀 것이다 — 두 스킬은 서로의 코드를 싣지 않고, 같은 사실은 아래
스킬인 스캔에 원본을 둔다. 고칠 때는 원본을 고치고 베낀다. claude 를 찾고 · 살폈나 보는 몸은 이 스킬만의 것이라 `unattended/launch_base.py` 가, 떼어 띄우는 인자는 창 곁의 손을 띄우는 넣는 손도 쓰므로
`scripts/detach.py` 가 든다(창 없는 몫은 `proc_base.quiet` 에서 얹는다).

**공통** — 각 명령이 `--dir <사용자 폴더>` 를 받는다(`cli.Once`). `tick` 은 필수 · 그 밖은 없으면 `scan.py status --json --dry-run` 의 `home` 을 쓴다(스캔
자리의 사본을 안 든다). 사람이 읽는 끝 줄은 `[보고 예약 — …]` · `[자리 밖에서 보기 — …]` · `[예약 — …]` · `[시계 — …]` 머리를 달고, 종료 값은 0 됐다 · 1 멈췄다(끝 줄이
다음 걸음을 말한다) · 2 인자가 틀렸다(`handed.py` 는 아래 따로). `tick` 밖의 명령이 사용자 폴더를 못 정하면 `[시계 — 사용자 폴더를 못 정했다 — …]` 한 줄과
1 로 끝난다.

#### `clock.py` — 정한 시각의 시계

| 명령 · 인자 | 내는 것 | 종료 값 |
|---|---|---|
| `tick --dir D --hand H` | 작업 스케줄러가 주기마다 부르는 한 판(작업의 명령줄이 이 두 인자를 굳힌다 — 밖에서 기대는 꼴이라 안 바꾼다). OS 잠금(`daily-brief-clock.lock`)을 못 쥐면 아무것도 안 내고 0. 판 끝에 줄을 차례로 낸다 — 자리 밖 메일 · 창의 고름 · 띄움 또는 기다림 · 누름 거둠(할 말이 없는 줄은 뺀다). 청한 판이 못 돌았으면 `[보고 예약 — {t} 보고: 메일함 스캔 한 판을 못 받아 못 띄웠다({앞 판이 시한 안에 안 끝났다 \| 스캔이 멈췄다 \| 스캔을 못 불렀다}) · {끝} 까지 다음 확인에 다시 청한다]`. 그날 장부를 그 순간 못 읽으면 판을 쉬고 `[보고 예약 — 그날 장부를 그 순간 못 읽었다({까닭}) — 이 판은 쉬고 다음 확인에 다시 본다]` | 0 · 1 시계가 스캔 · 손을 못 찾았다(`[시계 — …]`) · 그날 장부를 못 읽었다 · 2 |
| `register [--at [HH:MM …]] [--hand H] [--claude C] [--dry-run \| --validate]` | 작업 `\mail-secretary\daily-brief` 를 건다 — 주기는 시계의 것(`CLOCK_EVERY_MIN`)이고 손은 `--hand` · 없으면 형제 스킬 company-mail 의 `mail.py`. 메일함 스캔의 작업에 안 기댄다. 건 줄 `[예약 — daily-brief 시계를 걸었다: {n}분마다 · 앞 판이 돌면 그 주기는 건너뛴다]`. `--at` 이 있으면 이어서 `at` 과 같은 줄. `--dry-run` 이면 `[예약 — 걸지 않고 보이기만 한다. 걸면 시계 판이 {n}분마다 돈다(앞 판이 돌면 그 주기는 건너뛴다): {명령}]` 다음에 정의 틀. 손이 없으면 `[예약 — 걸지 않았다: …]` 로 멈춘다 | 0 · 1 · 2 |
| `at [HH:MM …] [--claude C] [--dry-run]` | 보고 시각표를 걸고 바꾼다(시각은 전부 준다 · 안 주면 기본 시각 하나). `[보고 예약 — …]` 건 줄 · 거절 줄, `--dry-run` 이면 띄울 명령 · 로그인 · 열린 · 막은 명령 줄. 시계가 안 걸려 있으면 끝에 `  ⚠ 시계가 안 걸려 있어 이 보고는 안 뜬다. 다음: clock.py register` | 0 · 1 |
| `off [--dry-run]` | 보고 예약을 내린다 — `[보고 예약 — 내렸다]` + 열린 창에 알린 구절 · `[보고 예약 — 걸려 있지 않았다]` · `--dry-run` 이면 내리지 않고 보이는 줄 | 0 |
| `away on\|off [--chosen-at 때] [--dry-run]` | 자리 밖에서 보기를 켜고 끈다. `--chosen-at` 없이는 `[자리 밖에서 보기 — {말}]`(켤 때 `· 받는 분 · 보내는 분 본인({주소})`)+ 창 알림 구절, 있으면 창에 적을 말 한 줄만(창 곁의 손이 부른다) | 0 따랐다 · 1 안 따랐다 |
| `window-times HH:MM [HH:MM …] [--window-base [HH:MM …]] --chosen-at 때` | 보고 창에서 고르신 시각을 건다(창 곁의 손이 부른다) — 그 창에 적을 말 한 줄(`--chosen-at` 이 없으면 `고르신 때가 없어 걸지 않았습니다 — 대화에서 말씀해 주세요`) | 0 따랐다 · 1 안 따랐다 |
| `status [--dry-run]` | 시계 작업 줄(`[예약 — daily-brief · 간격 … · 켜짐 … · 한 번에 하나 …]` + `  부르는 것: …` · `--dry-run` 이면 묻지 않는 줄)과 그 뒤 보고 예약 줄 전부(`brief_status.describe` — 시각마다 오늘 어떻게 됐나). 보고 예약 줄의 「작업이 안 걸렸다」는 시계 작업을 말한다. 시계가 없고 옛 보고 시각표만 있으면 `[시계 — 걸려 있지 않다 · 옛 보고 시각표가 있다 — 다음: clock.py adopt]`(모델이 이 줄로 `adopt` 를 부른다) | 0 |
| `unregister [--dry-run]` | 시계 작업을 지우고 보고 예약을 내린다 — 쌓인 파일은 안 건드린다. `[예약 — daily-brief 시계를 껐다{ · 보고 예약도 내렸다}]` · 못 껐으면 `[예약 — 못 껐다(걸린 작업이 없을 수 있다){ · 보고 예약도 내렸다}: {끝 300자}]` | 0 · 1 |
| `adopt [--dir D]` | 설치 · 대화가 부른다(설치는 업데이트 때 한 홈에서만 — 스캔의 `scan.py adopt` 와 차례에 안 기댄다). 메일함 스캔의 작업은 안 본다 — 옛 파일을 옮겨 받고(아래 파일 표) 걸린 시계만 본다: **다른 홈의 입구나 다른 손을 부르면 켜짐을 지켜 시계의 주기로 이 홈의 입구 · 이 홈의 회사 메일 손으로 다시, 없으면 보고 시각표가 있을 때만 시계의 주기로 새로**(손은 형제 스킬 company-mail 의 `mail.py` · 시각 · claude 는 사용자 폴더의 시각표 그대로). 여러 번 불러도 같다. 끝 줄 하나 — `[시계 — 걸었다 · 옛 보고 시각표를 옮겨 받았다]`(이번에 옛 시각표를 옮겨 받아 새로 걸었다) · `[시계 — 걸었다]`(있던 시각표로 새로 걸었다) · `[시계 — 이 홈으로 다시 걸었다{ · 꺼 둔 채로}]` · `[시계 — 이미 걸려 있다]`(이미 이 홈의 입구와 손을 부른다) · `[시계 — 건드리지 않았다: 걸린 시계의 명령줄이 거는 꼴이 아니다(손으로 고친 작업이다)]` · `[시계 — 걸 것이 없다: 시계가 안 걸려 있고 보고 시각표도 없다]` · 걸어야 하는데 못 걸었으면 `[예약 — 작업 스케줄러가 거절했다: …]` · `[시계 — 못 걸었다: …]`(이 홈의 회사 메일 손이 없다) · `[시계 — 사용자 폴더를 못 정했다 — …]` | 0(건너뛴 갈래 전부 · 걸었다) · 1 걸어야 하는데 못 걸었다(작업 스케줄러가 거절 · 메일 손이 없다 · 사용자 폴더를 못 정했다) · 2 |
| `lend --why put\|appr\|run --ceiling S [--lost] [--dir D]` | 보고 창 곁의 손(`presses.Borrow`)이 단추의 일이 세션 없음을 낸 뒤 부른다. 그 일이 사내 세션을 쓴다고 적고(쓸 끝은 `S` 초 뒤), 끊겼으면 오늘 이 PC 가 로그인을 돌려준 뒤일 때만 입구를 사람 없는 꼴로 한 번 부른다(위 「사람의 로그인을 돌려준다」). 끝 줄 하나 — `[보고 창 — 산 세션에서 한다]` · `[보고 창 — 사내 세션이 없어 빌리지 않았다]` | 0 산 세션에서 하면 된다 · 1 안 빌렸다 · 2 |
| `release --why put\|appr\|run [--hold] [--futile] [--dir D]` | 그 일이 끝난 뒤 부른다. 쓰는 일을 걷고(`--hold` — 띄운 결재 창이면 `GIVE_BACK_AFTER_MIN` 분 더 쓴다 · `--futile` — 빌린 로그인 위에서도 세션 없음이었다: 그 일에는 오늘 다시 안 빌린다), 빌린 로그인을 쓰는 일이 더 없고 시계가 띄운 보고도 안 돌면 곧 돌려준다. 끝 줄 하나 — `[보고 창 — {돌려준 끝}]` · `[보고 창 — 놓았다]` | 0 · 2 |

`at` · `off` · `away` · `window-times` 의 열린 창 알림 구절(`tell_window`)은 창의 알림(`state.sync`)을 스킬 안 함수로 부른 글이고, 안 열렸으면 빈 글이다.

#### `handed.py` — 맡긴 일

창 곁의 손(`runs.py`)이 보고 창에서 맡기신 일을 넘기고 따르는 문이다. 기록의 칸과 상태 낱말은 이 표와 「맡긴 일의 파일과 기록」이 원본이다(`format` 1). 종료 값 — 0 · 2 인자(맡긴 일 파일의 꼴 · 그런 판이 없다) ·
5 못 맡긴다(작업 폴더 · claude · 메일 손이 없다 — 기록을 안 쓴다).

| 명령 · 인자 | 내는 것 |
|---|---|
| `start --tasks <파일> [--work <폴더>] [--claude C] [--hand H] [--dir D]` | 곧 돌아와 기록 하나(JSON 한 줄) · 못 맡기면 `{"cannot": …}` · 꼴이 틀리면 `{"error": "args", …}`. 손은 `--hand` · 없으면 형제 스킬 company-mail 의 `mail.py`, claude 는 `--claude` · 보고 예약에 건 것 · PATH. 지킴이 명령줄은 `handed.py watch --id <판> --dir <사용자 폴더>` |
| `show --id <판> [--dir D]` | 그 판의 지금 기록(JSON 한 줄). 새 자리 `daily-brief-handed/` 에 없으면 옛 자리 `mailbox-scan/handed/` 도 읽는다 |
| `list [--dir D]` | 아직 도는 판의 기록 — 줄마다 하나(새것부터), 두 자리를 합쳐 |
| `watch --id <판> [--dir D]` | 지킴이 — `start` 가 떼어 띄운다. 아무것도 안 낸다 |

#### 스캔의 두 문 — 시계가 아래로 부른다

| 문 | 시계가 쓰는 것 | 꼴의 원본 |
|---|---|---|
| `scan.py run --now --wait <초> --hand H` | 보고 시각의 칸에서만, 그 칸에 한 번 청한다. 판의 갈래(`--full` · `--new`)와 `--full-every` 는 주지 않는다 — 스캔이 제 기본 전체 주기로 갈래를 고르게 해, 메일함 전체를 볼 때가 찬 보고 시각에 청한 판이 그것을 다음 정한 판으로 미루지 않는다(미루면 띄운 보고가 낡은 「메일함 전체를 마지막으로 다 본 때」를 읽는다). 전체 주기는 앞 판이 받아 적은 값이나 스캔의 기본을 따른다(스캔 설계 「status --json · run --wait」). `--wait` 는 늘 준다 — 값 `SCAN_WAIT_S = 900`(스캔의 한 판이 손을 부르는 시간의 한계 안), 부름의 시한은 `SCAN_CALL_TIMEOUT_S = 2400`(기다림 + 가장 긴 한 판). 낸 글은 안 읽는다 — 돈 판은 아래 `status --json` 으로 읽는다 | 스킬 mailbox-scan 설계 「status --json · run --wait — 프로그램이 기대는 꼴(원본)」 |
| `scan.py status --json [--dry-run]` | `home` · `last_run.started` · `last_run.session` 만 읽는다(`task` 칸은 안 읽는다 — 시계는 스캔 작업에 안 기댄다) — 청한 뒤 시작한 판이고 세션 답이 `live` 일 때만 띄운다 | 같은 곳(칸은 거기서 읽는다 · 여기 옮기지 않는다) |

#### 새 파일 이름 — 사용자 폴더 바로 밑, `daily-brief-` 머리

| 이름 | 든 것 | 옛 자리(없을 때만 읽어 옮겨 받는다 — 옛 것은 안 지운다) |
|---|---|---|
| `daily-brief-schedule.json` | 보고 시각표 · claude · 자리 밖 · 고른 것 · 스스로 로그인한 범위 | `mailbox-scan/brief.json` |
| `daily-brief-day.json` | 그날 장부(옛 `state.json` 의 `brief` 칸과 같은 꼴) + 시계의 마지막 판 때 `clock_at`(UTC ISO 8601 · 판마다 잠금을 쥔 뒤 적는다 — 창의 `seen` 이 읽는다) | `mailbox-scan/state.json` 의 `brief` 칸 |
| `daily-brief-launch.json` | 띄운 보고의 때 · 프로세스 번호 | `mailbox-scan/brief.lock` |
| `daily-brief-launch-settings.json` · `daily-brief-launch-prompt.txt` · `daily-brief-launch.log` | 띄울 때마다 새로 쓰는 설정 · 부탁 글 · 출력 | `mailbox-scan/brief-settings.json` · `brief-prompt.txt` · `brief-run.log` |
| `daily-brief-away-sending.json` | 보내는 중 표지 | `mailbox-scan/away-sending.json` |
| `daily-brief-away-me-*` | 주소록 「나」의 임시 폴더(옮겨 받을 것 없다) | `mailbox-scan/away-me-*` |
| `daily-brief-handed/<판>/` | 맡긴 판의 기록 · 맡긴 일 · 부탁 글 · 흐름(도는 판은 옛 자리에 둔 채 읽는다) | `mailbox-scan/handed/<판>/` |
| `daily-brief-clock.xml` · `daily-brief-clock.lock` | 시계 작업 정의의 사본 · 시계의 OS 잠금(`oslock.py`) | — |
| `daily-brief-loan.json` · `daily-brief-loan.lock` | 오늘의 돌려준 끝들 · 단추가 빌린 로그인 · 그 세션을 쓰는 일들(`loan.py` 하나가 쓴다) · 빌리고 돌려주는 OS 잠금 | — |

옮겨 받기는 `adopt` 와 시계의 첫 `tick` 이 같은 함수 하나로 한다 — 새 파일이 없고 옛 파일이 있을 때만 읽어 새 이름으로 바꿔 끼워 쓰고, 새 파일이 있으면 옛 것을 다시
안 본다. 작업 폴더의 `handed/<판>/`(맡긴 실행이 쓴 파일) · `daily-brief-prefs.md` · `daily-brief-entries.json` · `daily-brief-runs.json` · `brief-*.html` · `brief-*.md` 는 그대로다.

#### 맡긴 일의 파일과 기록 — `handed.py` 가 읽고 내는 것(원본)

위 `handed.py` 표가 말하는 맡긴 일 파일 · 기록의 칸과 상태 낱말의 원본은 이 절이다.

작업 폴더는 `--work`, 없으면 사용자 환경값 `PAISETUP_WORK`(레지스트리를 먼저, 그다음 프로세스 환경 — 보고 창 머리의 여는 손과 같은 차례)다.
claude 는 `--claude` · 보고 예약에 건 claude · PATH 차례, 메일 손은 `--hand` · 없으면 형제 스킬 company-mail 의 `mail.py` 로 찾는다.

**맡긴 일 파일**(UTF-8 JSON) — 값은 손대지 않고 실행에 그대로 싣는다. 적힌 차례가 하는 차례다.

| 칸 | 꼴 | 뜻 |
|---|---|---|
| `brief` | 글(빈 글 됨) | 부르는 쪽의 열쇠 — 기록에 옮길 뿐이다. 창 곁의 손은 누름의 열쇠를 실어, 답을 못 받은 판을 `handed.py list` 에서 찾는다 |
| `tasks[]` | 하나 이상 | 맡긴 일 |
| `tasks[].id` | 빈 글 아님 · 겹치지 않음 | 부르는 쪽의 열쇠 — 이 손에게는 뜻 없는 글이다. 기록이 그대로 돌려준다 |
| `tasks[].kind` | 빈 글 아님 | 일의 종류 낱말(보고 글의 「바로 할 일」 첫 칸) — 실행에 그대로 준다 |
| `tasks[].line` | 빈 글 아님 | 사람이 누른 줄의 값 그대로 |
| `tasks[].card.title` · `.lines[]` | 글 · 글 목록 | 카드의 머리와 딸린 줄 — 보고 글에 적힌 그대로(`(mail:번호)` 가 든다) |
| `tasks[].labels` | 빈 글 아닌 글 목록(없으면 빈 목록) | 결과의 `facts` 에 쓸 이름표 — 그 차례로 실행에 준다 |

**기록**(`show` · `list` · `start` 가 내는 JSON)

| 칸 | 꼴 | 뜻 |
|---|---|---|
| `format` | 1 | 꼴 번호 — 칸의 뜻을 바꾸면 오른다 |
| `id` · `brief` | 글 | 판의 열쇠 · 맡긴 일 파일의 `brief` |
| `started` · `ended` | UTC ISO 8601(천분의 일 초) · 도는 중이면 null | 맡긴 때 · 맺은 때 |
| `alive` | 참 · 거짓 | 아직 도나(`end` 가 null 이다) |
| `end` | null · `finished` · `login` · `died` · `cut` | 다 했다 · 로그인 끊김(띄우기 전이나 도중) · 죽었다(claude 가 오류로 끝났다 · 지킴이가 없다 · 띄우지 못했다) · `CEILING_S` 를 넘겨 끊었다 |
| `said` | 글 | 다 하지 않은 끝의 까닭 — claude 의 오류 출력의 끝 따위. 다 했으면 빈 글 |
| `session` | 글 · null | claude 의 세션 번호 — VS Code 의 작업 폴더 창에서 그 대화를 잇는다. 띄우고 첫 줄이 오면 선다. 실행은 띄운 쪽의 이름(`ENTRYPOINT` — 환경값 `CLAUDE_CODE_ENTRYPOINT`)을 사람이 이어 갈 대화의 것으로 세션에 적는다 — `claude -p` 가 스스로 적는 `sdk-*` 이면 VS Code 확장이 그 세션을 목록에서 빼 `session=` 이 새 대화를 연다(문서에 없는 값에 기댄 우회 — 확장이 `-p` 세션을 목록에 넣으면 걷는다) |
| `model` · `cost` · `turns` | 글 · 수 · 수 | 돈 모델(첫 줄이 오면 선다) · 값(USD) · 턴 수(둘은 맺기 전 null) — 이은 실행까지 더한 것 |
| `resumed` | 수 | 같은 세션을 이어 남은 일을 하게 한 수(0 · 1) |
| `end_text` | 글 | 실행의 끝말 그대로(맺음 사건의 글) — 표지 없이 끝난 판에서 사람에게 보일 거리 |
| `work` · `files` | 경로 | 작업 폴더 · 이 판이 쓴 파일의 자리 |
| `tasks[]` | 맡긴 차례 그대로 | 일마다 하나 |
| `tasks[].id` · `.kind` | 맡긴 그대로 | |
| `tasks[].state` | `waiting` · `doing` · `done` · `asked` · `failed` · `unknown` | 기다림 · 하는 중 · 됨 · 여쭐 것(그 일만 멈췄다 — 대화로 이어 간다) · 못 함 · 확인 안 됨(들었는지 모른다) |
| `tasks[].at` | UTC ISO 8601 · null | 그 상태가 된 때 — 됨 · 여쭐 것 · 못 함 · 확인 안 됨은 표지가 온 때(표지 없이 맺은 판은 맺은 때), 하는 중은 앞 일의 끝 |
| `tasks[].text` | 글 | 결과 글 — 실행이 표지 뒤에 쓴 그대로(표지만 뺀다 — 표지 줄의 남은 글은 든다) |
| `tasks[].result` | 객체 · null | 결과 글이 꼴(JSON 객체 하나 — 코드 블록 하나로 감싸도 된다)이면 그 칸 — `said` 글 · `facts` [[이름표, 값]] · `items` [{`label`, `unid`, `note`}] · `more` 글(빈 칸은 뺀다 · `said` · `facts` · `items` 가운데 하나는 있다). 꼴이 아니거나 표지 없이 맺은 일이면 null |

## 하지 않는 것

- **메일함 · 일정을 스스로 바꾸지 않는다** — 바꾸는 것은 사람이 창에서 누른 「일정 넣기」 한 건(그 카드의 값과 열쇠로만)과 사람이 누른 맡길
  일(뒤의 실행이 한다)뿐이다. 사람 없는 보고는 미리 보기 · 빈 방 찾기까지만 부른다
- **창에서 받지 않는 것** — 보고를 걸고 내리기 · 띄울 claude · 메일함 · 업무 파일 · 받는 분의 주소. 사람 없는 보고를 거는
  확인은 대화에서 받은 승인이라 창의 누름 하나로 넓히지 않는다
- **보내지 않는다** — 부탁은 입력 칸을 채우기까지(엔터는 사람), 메일 한 장은 짓기까지(보내는 것은 시계), 맡길 일의 답장은 임시
  보관까지(뒤의 실행 — 「맡긴 일의 실행」)다
- **모델의 판단을 다시 하지 않는다** — 맡길 일의 종류를 짐작하거나 줄을 고치지 않고, 「보고에서 빼는 것」의 갈래를 가르지 않고, 친 말 · 결과
  글을 읽어 무엇을 가르지 않는다. 꼴이 틀린 줄은 글로 세우고 그렇다고 말한다
- **창과 창 곁의 손은 스스로 로그인하지 않는다** — 사내 로그인이 끊긴 누름은 남겨 두고 살아난 세션에서만 다시 해 본다. 사람 없이 로그인하는 것은
  보고 시각을 건 PC 의 시계뿐이다 — 보고 시각의 칸 안에서와(위 「사내 세션과 스스로 로그인」), 그날 그 로그인을 돌려준 뒤 누른 단추를 할 때
  시계의 `lend` 로 잠깐 빌리는 것뿐이다(위 「사람의 로그인을 돌려준다」)
- **사람의 Edge 에 탭을 함부로 열지 않는다** — 창 이음 명령 · 알림은 열린 보고 창에만 적는다. 탭을 여는 것은 창을 띄울 때와, 열린 file: 탭이
  없을 때 거두는 손이 뒤 탭을 잠깐 열고 닫을 때뿐이다

## 검사가 남는 까닭 — 설정 저장소의 `_check/skills/daily-brief/check_window.py`

판정마다 check-design 1 절의 넷:

| 판정 | 길 | 조용하다 | 다친다 |
|---|---|---|---|
| 창의 스크립트가 돈다 | 창의 스크립트는 한 스코프의 큰 글이라 두 단추의 손이 같은 이름을 쓰면 뒤 선언이 앞을 덮는다  | 눌린 단추는 눌린 꼴만 보이고 아무것도 안 남긴다. 창을 짓는 쪽의 검사는 스크립트를 돌리지 않아 다 초록이다 | 끝났다고 누르신 일이 날마다 다시 올라오고 미루신 일 · 맡기신 일이 사라진다 |
| 창의 스크립트가 돈다 — 연락이 끊겨도 맡긴 누름을 맺지 않는다 | 창 곁의 손만 죽고 뒤의 실행은 살아 있는 판이 난다(손은 창과 함께 닫히고 실행은 따로 떼어 띄운다) — 창이 숨 표가 끊긴 것을 「멈춤」으로 읽으면 끝을 지어 적는다 | 판이 끝나면 손이 돌아올 때 바로잡혀 만드는 쪽의 판에서는 안 보인다. 사람 자리에서만 「하지 않았습니다 — 바뀐 것은 없습니다」 와 「다시 맡기기」 가 선다 | 그 말을 믿고 다시 맡기거나 손으로 하면 같은 회의실이 두 번 잡히고 다른 분들께 안내 메일이 두 번 간다 — 되돌릴 수 없다 |
| 링크는 메일 번호에서만 · 글은 글자로 · 메일함 주소의 꼴 | 줄 안의 꼴을 읽는 손 · 메일함 주소를 대는 손을 고칠 때마다 — 보고 글은 모델이 메일을 읽고 쓴 글이라 메일 속 주소 · HTML 이 그대로 실린다 | 모델이 쓴 주소로 간 링크도 메일 링크와 똑같이 생겼다 | 사용자가 누른 링크가 메일 속 낚시 주소로 가거나, 메일 속 글이 창에서 HTML 로 돈다 |
| 절 수가 달라도 선다 · 줄이 다 선다 | 덩이를 가르는 손을 고칠 때마다 — 절 · 줄은 사람마다 · 날마다 다르다 | 줄 없는 절이 다음 절의 줄을 먹거나 줄이 빠져도 창은 멀쩡히 선다 | 보셔야 할 줄이 창에서 사라진다 |
| 생김새는 그 꼴의 줄에서 | `lane.md` 의 「보고 글의 꼴」과 스크립트는 따로 고쳐진다 | 스크립트가 안 읽는 표시는 글자로 서서 창은 뜬다 | 메일 줄이 링크가 안 되고 기한 지남 표지가 안 선다 |
| 바깥을 안 부른다 · 스크립트는 해시 하나 | 틀을 디자인 시안에서 다시 뜰 때마다 — 시안은 바깥 글꼴 · 스크립트를 부른다. 창의 스크립트를 고칠 때마다 | 바깥에 닿는 PC 에서는 멀쩡하고 사내망에서만 꼴이 무너진다. 해시가 갈리면 창은 멀쩡히 뜨고 상자만 안 선다 | 메일에서 온 글이 든 창이 바깥에 요청을 내거나 그 글이 스크립트로 돈다 |
| 홀로 선다 · 메일함에 안 닿는다 | 스킬에 코드를 더할 때마다 — 다른 스킬 · 앱의 코드를 싣는 것이 가장 가까운 길이다. 열린 망 모듈은 디버깅 포트로 가는 둘(http.client · socket)과 주소를 푸는 `urllib.parse` 뿐이고, 잇는 곳은 늘 `EDGE_HOST` 다. 다른 프로그램은 넣는 손의 세 자리(카드의 값으로 일정 손 — 마무리의 미리 보기 · 누른 카드의 넣기가 다 `run_calendar` 한 자리로 간다 · 창 곁의 손 · 같은 스킬 `unattended/` 의 입구 — 「자리 밖에서 보기」 · 보고 시각 고름 · 맡긴 일은 다 `run_unattended` 한 자리로 간다)에서만 이 파이썬으로 정해 둔 스크립트를 띄우고(명령줄은 프로세스 바탕의 `python_argv` 가 짓는다 — 그 바탕의 아무 스크립트나 받는 `run_python` 은 창의 손이 안 부른다 · 떼어 띄우는 인자 `detach.py` 는 아무것도 안 띄운다), 여는 손은 등록된 VS Code 에 작업 폴더 하나만 주며(`raise_folder`) 주소는 `link(…)` 가 지은 것만 연다(`take`) | 링크를 미리 불러 보는 손은 메일을 다 읽음으로 바꾼 채 아무 말도 안 한다 | 실린 쪽이 바뀔 때마다 스킬이 깨지거나 안 읽은 메일이 몰래 읽음이 된다 |
| 보고 글이 창 곁에 남는다 | 창을 쓰는 자리 · 파일 이름을 고칠 때마다 | 창은 멀쩡히 뜨고 다음 날 보고만 지난 보고를 못 찾는다 | 이 글이 다음 보고의 유일한 기록이다 — 끝난 일이 다시 올라오고 기다리던 답을 놓친다 |
| 끝의 절 · 기록 절을 잇는다 | 스킬 글이 대는 절의 이름과 스크립트가 찾는 이름은 따로 고쳐진다 · 기록 절은 새 보고 글마다 이어져야 하는데 모델에게 맡기면 한 번 빠뜨리는 날 끊긴다 | 이름이 갈리면 경고가 날마다 헛울리고, 경고를 걷으면 절이 빠져도 아무도 모른다. 기록 절이 빠진 새 글도 창은 멀쩡하다 | 다음 업무 파악이 끝났다고 하신 일을 못 닫아 날마다 다시 올라오고, 끝나지 않았다고 되돌리신 일이 닫힌 채 남는다 |
| 창은 로그인 Edge 로 · 꼬리 | 창을 여는 손을 고칠 때마다 | 새 탭이 안 서도 기본 브라우저가 창을 대신 연다. 꼬리가 빠지면 상자가 조용히 사라진다 | 메일 링크마다 로그인 창이 떠 보고 창이 한 번에 메일을 못 연다 · 거둘 수 없는 창에서 누른 표시가 사라진다 |
| 누름 단추 | 줄을 짓는 손을 고칠 때마다 — 카드와 줄은 같은 일을 다른 꼴로 세운다 · 근거 메일이 여럿인 카드에서 첫 링크가 그 일의 메일이 아닌 꼴을 모델이 쓴다 | 엉뚱한 메일 번호로 선 단추도 똑같이 눌린다 | 누르신 일 대신 다른 일이 업무 파일에서 닫히거나 감춰져, 보셔야 할 일이 보고에서 사라진다 |
| 표시를 거둔다 | 거두는 손 · 보고 글의 절을 찾는 손을 고칠 때마다 | 표시를 잃거나 두 번 더해도 아무 말이 없다 | 끝내신 일이 날마다 다시 올라오거나, 다음 보고의 유일한 기록인 보고 글이 깨진다 |
| 내일 다시 | 돌아오는 날 · 다시 올린 것을 걷는 때를 가르는 손을 고칠 때마다 · 거두기만 하고 보고가 안 지어지는 판(세션이 끊긴 사람 없는 보고 · 멈춘 하위 에이전트)이 있다 | 너무 일찍 돌아와도 영영 안 돌아와도, 돌아온 줄이 보고 없이 사라져도 창은 멀쩡하다 | 미루신 일이 오늘 또 서거나, 미룬 채 잊혀 기한을 넘긴다 |
| 이런 건 빼기 | 맞춤 파일의 꼴 · 되돌리는 열쇠를 고칠 때마다 | 감춘 줄이 안 보이거나 되돌림이 안 먹어도 아무 말이 없다 | 사람이 무엇을 감췄나 못 읽고 못 되돌려, 보셔야 할 일이 보고에서 영영 빠진다 |
| 사람별 | 칸을 읽는 손을 고칠 때마다 — 덧말 속 「 · 」를 사람의 가름으로 읽으면 없는 사람이 선다 | 사람이 빠지거나 없는 사람 · 끝난 일의 사람이 서도 창은 멀쩡하다 | 기다리시는 분을 못 보고 답이 늦는다 |
| 보고 맞추기 | 시각표 · 맞춤 파일을 읽는 손을 고칠 때마다 — 이미 건 PC 는 옛 꼴을 든다 | 칸이 비거나 고르는 칸이 숨지 않아도 창은 멀쩡하다 | 걸린 시각과 감춘 것을 못 보거나, 거둬지지 않는 창에서 고르신 것이 사라진다 |
| 스스로 로그인해 지은 보고의 한 줄 | 시계가 적은 범위를 읽는 손 · 범위를 재는 손을 고칠 때마다 — 그 범위는 로그인할 때마다 새로 적히고 지난 범위가 파일에 남는다 | 줄이 안 서도 · 지난 범위에 서도 창은 멀쩡하다 | 사람이 포털에서 앱이 왜 안 뜨는지 모르거나, 로그인 없이 지은 보고마다 로그인을 새로 했다는 줄이 서 사람이 까닭 없이 「EP 돌려줘」를 청하고 그 돌려주기가 비서 쪽 세션을 끊는다 |
| 일정에 넣기 카드 | 칸을 읽는 손 · 「무엇을 넣나」의 말을 고칠 때마다 — 창과 넣는 손이 같은 칸을 읽는다 · 열쇠는 열여섯 글자의 해시라 옮겨 적는 손이 끼면 한 글자씩 틀린다 · 모델은 회의 절 이름을 그날에 맞게 바꿔 쓴다 | 공개 범위 · 날을 잘못 적어도 단추는 똑같이 눌린다. 열쇠가 틀리면 누른 뒤에야 「그 사이 바뀌어」라는 거짓 말이 선다 | 사람이 「공개 · 목요일」을 보고 눌렀는데 다른 꼴로 남이 보는 회사 일정에 든다 · 약속이 안 들고 일어나지 않은 바뀜을 믿는다 · 회의를 누르면 요청 메일의 일이 닫힌다 |
| 맡길 일 | 줄을 읽는 손 · 미리 가르는 손 · 창 곁의 손이 따로 고쳐진다 — 사람이 누르는 것은 번호이고 손은 그 번호로 글의 줄을 찾는다 | 번호가 갈려도, 틀린 줄에 단추가 서도 창은 멀쩡히 눌린다 | 사람이 본 줄과 다른 일이 되거나(참석자 없는 회의실 · 다른 카드의 일), 안내 메일이 사람이 고르지 않은 분께 간다 |
| 맡긴 일은 한 번 | 창 곁의 손 · 창 · 뒤의 실행이 따로 돈다 · 손이 죽었다 다시 뜨거나 창이 손을 잃어 맺은 누름이 실제로 생긴다 · 같은 일을 「다시 맡기기」 · 「이것만 맡기기」로 또 누를 수 있다 | 다시 넘긴 일도, 덮인 기록도 창에는 멀쩡히 선다 | 같은 회의실이 두 번 잡히고 다른 분들께 안내 메일이 두 번 가거나, 된 일이 「못 함」으로 서서 또 맡기게 된다 |
| 누름 하나 맺기의 차례 | 누름 하나 맺기를 가르고 고칠 때마다 차례가 옮길 수 있다 — 견줌 판 · 「누른 그 한 건만」의 흉내는 부르기 직전의 취소와 기록 쓰기 실패를 못 짓는다 | 취소된 누름이 들어도 · 「넣는 중」 없이 불러도 창은 「넣었습니다」만 보인다 | 사람이 거둔 약속이 남이 보는 회사 일정에 들거나, 넣다 끊긴 판에서 들었는지 모르는 일정이 기록 없이 남아 또 넣게 된다 |
| 시한을 넘긴 넘기기 | 맡긴 일 넘기기가 시한을 넘기는 판이 실제로 생긴다(바쁜 PC) — 흉내는 프로세스 시한을 못 짓는다 | 「못 함」으로 맺어도 창은 멀쩡히 「다시 맡기기」를 세운다 | 넘겨진 일을 사람이 또 맡겨 같은 방이 두 번 잡히고 안내 메일이 두 번 간다 |
| 누른 그 한 건만 한 번 | 넣는 길이 둘(창 곁의 손 · 시계 판)이라 같은 누름을 함께 본다 · 넣다 끊긴 판이 실제로 생긴다(시한 · PC 꺼짐) · 창끼리 저장소가 하나라 다른 창의 같은 카드가 같은 열쇠로 다시 눌린다 · 세션이 끊긴 누름을 다시 해 보는 때를 두 길이 따로 정한다 | 두 벌 든 일정 · 안 누른 일정은 넣는 쪽에 아무 표도 안 낸다. 덮인 기록 · 안 다시 해 본 누름도 창은 멀쩡하다 | 남이 보는 회사 일정에 사람이 고르지 않은 건이 서고, 지운 일정은 되돌릴 손이 없다 · 넣은 약속이 「안 넣음」으로 보여 또 넣게 되거나, 「살아나면 넣는다」던 약속이 영영 안 든다 |

다른 무엇도 이 넷을 안 잰다.

**표본** — `lane.md` 「보고 글의 꼴」의 예(모델이 따라 쓰는 꼴 그대로 — 그래서 첫 표본이다)와, 그 꼴로 지은 가상의 하루 셋(끝의 두 절까지
갖춘 절 셋 · 줄 없는 절이 든 절 일곱 · 메일 속 주소와 HTML 이 든 날), 끝의 절을 뺀 날, 기록 절 둘을 든 지난 보고 글 뒤의 날(모델이 그 절을 안
옮긴 글 · 한 줄을 옮긴 글), Windows 도구가 cp949 · CRLF 로 쓴 날. 기대값은 표본을 지은 뜻과 꼴의 표시를 센 수와 계약(끝의 절의 이름 — 사용자가 정한
겉)에서 낸다.

**창을 짓는 자리** — 창 손은 늘 임시 스킬 뿌리의 사본으로 띄운다 — 곁에 가짜 일정 손(빈 일정)을 세운다. 마무리가 「일정 넣기」 줄마다 곁의
일정 손을 미리 보기로 부르는데, 저장소의 스킬 곁에는 진짜 일정 손이 있어 검사가 회사 일정 앱에 닿으면 안 된다. 열쇠 없이 쓴 줄에 서야 할
열쇠는 가짜 일정 손을 따로 불러 낸다(견줄 원본).

**판정 손을 안에 줄여 둔 까닭** — 씨앗 `seeds/check/_check/_verdict.py` 의 `report` · `edge` · `Unmeasured` 와 종료 값 셋을 받아 오지
못한다 — 푸시 문(`skill-checks`)이 내보내는 자리에는 스킬 폴더만 있다. 끝 줄은 형제 검사의 「통과 N/N」 꼴을 따른다.

**「홀로 선다」가 검사 파일을 안 훑는 까닭** — 검사는 손을 띄우고(subprocess) 가짜 포트를 세워(http.server · socket) 재고 금줄 낱말을 제
표로 들어, 훑으면 제 글에 걸려 늘 빨갛다.

**가짜 Edge** — 「표시를 거둔다」는 `/json/version` 과 CDP 웹소켓을 흉내 내는 가짜 포트에 거두는 손을 붙인다. 가짜는 file: 탭에서만
저장소를 보이고(about:blank 은 다른 저장소다) 답 앞에 사건을 끼운다 — Chromium 의 그 꼴이다. 창의 스크립트는 돌리지 못한다.

**가짜 일정 손** — 「누른 그 한 건만」은 임시 스킬 뿌리에 이 스킬의 사본과 가짜 일정 손(설정 저장소 `_check/skills/daily-brief/fake_calendar.py`)을
나란히 세워 잰다. 가짜는 판(값 · 겹침 · 이미 있나)의 해시를 열쇠로 내고 넣기(`add`)로 받은 인자를 다 적는다 — 넣는 손이 무엇으로 몇 번 불렀나를 그 기록으로
잰다. 그 판에서는 검사가 창 곁의 손의 잠금을 쥐어 손이 안 뜬다 — 뜬 손이 판 사이에 누름을 거두면 판이 갈린다. 창 곁의 손이 뜨고 끝나는지는
판정으로 두지 않는다 — 손이 안 끝나도 사람을 다치게 하는 일이 없다(시계 판이 같은 누름을 받고, 남은 손은 창이 닫히면 끝난다).

**가짜 시계** — 「내일 다시」는 누르신 때(`at`)와 보고 글 이름의 날을 옮겨 「다음 날 첫 보고」를 세운다 — 손에 시험만을 위한 시계 손잡이를 두지 않는다.

**버리는 Edge** — 「창의 스크립트가 돈다」만 진짜 Edge 를 버리는 headless 로 띄워 창의 스크립트를 CSP 아래에서 돌린다(스킬 글의 예로 지은 창 ·
제 프로필 · 남는 포트 · 띄운 Edge 는 판이 끝나면 거둔다). 손과 연락이 끊긴 창은 손이 맡은 누름 하나를 저장소에 두고 숨 표를 지운 뒤 다시 연 창의
시계만 숨 표 틈보다 앞당겨 만든다 — 기다리지 않는다. Edge 가 없는 PC 에서는 「못 쟀다」다.

**여기서 못 재는 것** — 창이 고른 디자인 그대로 보이나(사람의 눈이 가른다) · 기본 브라우저가 실제로 뜨나 · 진짜 Edge 에서 「창의 스크립트가
돈다」가 누르는 것(줄의 「끝났음」 · 카드의 「이것만 맡기기」 · 손과 연락이 끊긴 창) 밖의 단추와 칸(「내일 다시」 · 「이런 건 빼기」 · 「보고
맞추기」 · 「일정 넣기」 · 부탁 · 상태마다의 막대) · 회사 Edge 의 정책 아래에서 창의 스크립트가 도나(회사 판) · 모델이 「보고에서 빼는 것」의 보기로
같은 갈래를 가르나 · 메일 한 장이 휴대폰 메일 앱에서 그 꼴로 서나(회사 판) · 링크를 눌러 회사 웹메일에서 그 메일이 한 번에 열리나(회사 판) ·
모델이 스킬 글의 꼴대로 쓰나 · 다음 날 보고가 남은 글을 읽고 달라진 것만 보이나.

## 검사가 남는 까닭 — 설정 저장소의 `_check/skills/daily-brief/check_clock.py`

정한 시각의 시계는 가짜 메일 손 · claude 대역 · 로그인 입구 대역 · 가짜 스캔 위에서 돈다. 진짜 Edge 를 띄우는 창의 검사(`check_window.py`)와 무게와 층이
달라 한 파일에 안 섞고, 가짜 메일함과 대역은 스캔의 검사(`_check/skills/mailbox-scan/check_scan.py`)의 판 세우기를 경로로 싣는다. 기대값은 스킬 글과 이
문서의 문장, 판마다 심은 메일에서 낸다.

판정마다 check-design 1 절의 넷(길 · 조용하다 · 다친다 · 다른 무엇도 안 잰다):

| 판정 | 길 | 다친다 |
|---|---|---|
| 아침 보고 — 칸의 끝까지 기다림 · 끝 뒤 그만둠 · 한 번 · 틈 · 날마다 새로 | 살펴보기 · 띄우기의 갈래를 고칠 때마다(칸과 틈은 사용자가 정한 것이다) | 늦게 로그인한 아침에 보고가 안 뜨거나, 하루 내내 SSO 를 두드리거나, 보고를 여러 번 띄워 모델 값이 새고, 나쁜 하루 뒤로 보고가 영영 안 뜬다 |
| 보고 시각표 — 시각마다 한 번 · 옛 설정을 읽는다 · 창에서 고르신 시각 | 칸 · 그날 칸의 기록 · 설정의 꼴 · 창을 묻는 길을 고칠 때마다, 이미 건 동료 PC 는 옛 꼴을 든다 | 정한 시각에 보고가 안 서거나 두 번 서고, 판을 올린 동료 PC 의 보고가 조용히 멈추고, 창에서 고르신 시각이 영영 안 걸린다 |
| 보고 시각표 — 못 읽는 동안 한 칸만 바꿔 쓰는 명령은 안 쓴다 | 시계 판 · 창 곁의 손 · 대화가 같은 파일을 함께 쓰고, 윈도에서는 남이 바꿔 끼우는 순간의 읽기가 진다 | 시각표 · 스스로 로그인 · 자리 밖에서 보기가 빈 것으로 읽혀 덮이고, 사람 없는 PC 의 보고와 메일이 아무도 모르게 멈춘다 |
| 아침 보고 — 띄우지 않을 때 | 대화에서 이미 보고를 지은 날 · 지금 모습이 깨져 다시 지은 날은 늘 난다 | 같은 날 보고가 둘 서고 모델 값이 두 번 든다 |
| 아침 보고 — 읽는 명령만 연다 | 열린 명령 · 막은 명령 · 띄우는 인자를 고칠 때마다, 그리고 사용자 설정의 allow 가 함께 실린다 | 되돌릴 수 없다 — 사람 없는 실행이 메일을 보내거나 메일함 · 일정을 바꾸거나 로그인 · 문서함에 닿는다 |
| 아침 보고 — claude 없이 안 건다 | VS Code 확장만 깐 PC 는 PATH 에 claude 가 없다 | 걸린 줄 아는 보고가 날마다 안 뜨는데 아무도 모른다 |
| 아침 보고 — 업무 파일은 쓰는 손으로만 · 업무 파악부터 | 권한 · 부탁 글 · 도구를 고칠 때마다 | 되돌릴 수 없다 — 쓰는 손이 안 열리면 업무 파일이 날마다 안 고쳐지고, 파일 도구가 열리면 확인받은 절이 사람 없이 사라진다 |
| 스스로 로그인 — 보고 시각을 안 건 PC(스캔만 · 내린 PC)는 안 부른다 · 보고 시각을 건 PC 는 따로 켠 값 없이(옛 칸이 끔이어도) 첫 시각에 하루 한 번 사람 없는 꼴로(세션이 살아도 띄우기 앞에) · 서면 띄운다 | 세션이 없는 판은 아침마다 나고, 그 갈래와 시각표 파일의 꼴을 고칠 때마다 | 보고를 받지도 않는 사람의 메일을 판마다 끊거나, 보고 시각을 건 사람의 보고가 옛 칸 하나로 끊긴 세션에서 조용히 빠진다. 사람 있는 꼴로 부르면 로그인 화면이 사람을 기다리며 판을 막는다 |
| 스스로 로그인 — 보고 시각을 건 PC 의 뒤 시각은 세션이 끊겨 있으면 한 판 안에서 한 번 부르고, 서면 스캔에 한 판을 청해 산 세션에서 메일함을 읽은 뒤 그 판에 한 번 띄우며(칸의 마지막 판이어도 · 청한 판이 세션 없음이면 안 띄우고 그 칸에서 다시 안 부르며 뒤 판이 산 세션에서 읽으면 띄운다 · 청한 판이 건너뛰었으면 그 칸의 다음 판이 다시 청한다 · 못 세우면 그 칸에서 다시 안 부르고 status 가 까닭을 댄다) · 세션이 살아 있으면 안 부른다. 첫 시각도 같은 길로 청한 판이 읽은 뒤 띄운다 | 낮에 사람이 평소 Edge 에서 다시 로그인하면 비서 쪽 세션이 끊긴다 — 여러 시각을 건 사람에게는 날마다 날 수 있다. 첫 시각은 세션이 살아도 부르는 꼴이라 그 꼴을 뒤 시각에 옮기는 것이 가장 가까운 길이다 | 끊긴 세션에서 안 부르면 둘째 · 셋째 보고가 아무 말 없이 빠지고, 산 세션에서도 부르면 낮마다 까닭 없이 사람의 메일 · 일정 창이 닫히고 EP 포털이 죽는다. 한 칸에서 되풀이하면 판마다 그렇다 |
| 스스로 로그인 — 보고 시각 사이의 판(칸 밖 · 이미 띄운 칸)은 세션이 끊겨 있어도 안 부른다 | 보고를 띄운 뒤 사람이 평소 Edge 에서 다시 로그인하는 낮은 늘 난다 · 띄우기 앞의 갈래를 고칠 때마다 | 사람이 다시 로그인할 때마다 다음 판이 그 로그인을 도로 끊어, 몇 분마다 창이 꺼졌다 켜졌다 한다 |
| 스스로 로그인 — 세션 없이 스스로 로그인해 띄운 보고의 창에만 그 한 줄이 선다 | 시계가 남기는 칸(`unattended/`)과 창이 읽는 칸(`scripts/`)이 폴더를 달리해 따로 산다 — 한쪽의 이름 · 꼴을 고칠 때마다 | 창은 멀쩡히 뜨고 그 줄만 안 서 사람이 포털에서 앱이 왜 안 뜨는지 모르거나, 로그인 없이 지은 보고가 다시 로그인하라고 해 사람이 까닭 없이 비서 쪽 세션을 끊는다 |
| 보고 창의 「일정에 넣기」 — 판마다 거둔다 | 창 곁의 손이 없는 날(PC 를 다시 켰다 · 손이 죽었다)은 늘 난다 · 시계 판의 차례를 고칠 때마다 | 사람이 누른 약속이 들지 않고 창은 「다음 확인에」를 말한 채 남는다 |
| 시계 작업 — 한 번에 하나 · 준 주기 · 사용자 폴더와 손을 명령줄에 · 시작 때와 로그온 뒤 첫 판을 주기의 절반 늦게 | 시계 작업의 정의를 짓는 손(`clock_task.py`)이나 정의의 틀을 고칠 때마다 | 겹쳐 돌면 그날 장부가 엇갈리고, 옛 스캔 작업이 남은 PC 에서 같은 분에 깨면 청한 판이 「앞 판이 돈다」로 늦으며, 사람 PC 에 건 정의는 다시 걸기 전까지 그대로다 |
| 보고 시각표 — 기본은 07:30 하나로 12:00 까지 · 틈이 30분 안 되는 시각은 안 건다 · 12:00 뒤 시각도 걸린다 | 이름 붙은 값(`unattended_const.py`)을 고칠 때마다 | 걸린 줄 아는 시각이 날마다 조용히 안 뜨거나 아침 보고가 오후에 선다 |
| 옮겨 받기 — 메일함 스캔의 작업 없이 시계만 보고, 다른 홈을 부르는 시계는 켜짐을 지켜 시계의 주기로 이 홈의 입구 · 손으로 다시(시각표는 그대로) · 시계가 없으면 시각표가 있는 PC 에만 새로 · 이미 이 홈을 부르는 시계 · 손으로 고친 시계는 안 건드린다(가짜 작업 스케줄러 위에서) | 도구 홈이 여럿 깔린 PC 의 업데이트마다 · 시계를 건 홈이 걷힌 PC · 설치가 옛 스캔 작업을 먼저 거둔 PC | 시계가 옛 홈의 코드나 손을 불러 정한 시각의 보고가 옛 판으로 돌거나, 스캔 작업을 거둔 뒤 시계가 「걸 것이 없다」로 서지 않아 보고가 아무 말 없이 안 뜨고, 고르지 않은 PC 에 걸면 사람이 고르지 않은 시계가 돈다 |
| 옮겨 받기 — 옛 파일을 새 이름으로 · 옛 것은 그대로 · 그날 띄운 칸을 다시 안 띄운다 · 두 번 돌아도 같다 | 스캔이 보고를 들던 PC 마다 업데이트에서 한 번 난다(설치의 `adopt` · 시계의 첫 판) | 옛 시각표를 잃으면 보고가 조용히 끊기고, 그날 띄운 칸을 또 띄우면 같은 보고가 둘 서고 모델 값이 두 번 든다 |
| 홀로 선다 — `unattended/` 는 표준 라이브러리 · 제 폴더 · 같은 스킬의 `scripts/` 만 싣는다(예외는 보내는 손의 `mailer` 하나) | 형제 스킬의 코드를 싣는 것이 가장 가까운 길이라 코드를 더할 때마다 | 형제 스킬이 바뀌면 사람 없이 도는 시계가 아무도 모르게 죽는다 |
| 자리 밖에서 보기 — 켠 뒤 띄운 보고가 글을 남기고 끝난 칸을 보낼 칸으로 집고 끝을 적는다 · 메일 한 장을 못 지으면 「보내는 중」 표지 없이 다시 보낼 끝으로 남긴다 | 보낼 칸을 고르는 셈 · 표지의 차례를 고칠 때마다 | 보낸 메일은 되돌릴 수 없다 — 두 번 가거나, 안 간 채 간 줄 안다 |
| 돌려주기 — 스스로 로그인한 보고가 끝나고 10분 뒤 한 번 · 그 때에 깨는 한 번만의 작업 · 보고가 도는 동안 · 그 틈 안은 안 · 다시 안 · 살아 있던 세션 앞의 부름은 안 · SSO 가 안 서는 날은 한 번만 · status 가 댄다 | 세션이 끊긴 아침마다 동료 PC 의 시계가 사람 없이 돈다 | 안 돌려주면 평소 Edge 의 EP 포털이 하루 내내 죽어 ERP · MES 를 못 띄우고(보고는 서 조용하다), 일찍 돌려주면 보고 창의 단추가 세션을 잃고, 거듭 부르면 사람이 다시 한 로그인을 판마다 끊는다 |

모두 사람 없이 돌거나 틀린 셈도 그럴듯하게 서서 조용하고, 다른 무엇도 안 잰다.

**여기서 못 재는 것** — 작업 스케줄러가 시계 작업을 실제로 받나(`--dry-run` 의 정의와 가짜 작업 스케줄러 위의 `adopt` 만 잰다 — 꺼 둔 시계를 끈 채
다시 거는 갈래는 한 번 확인했다) · 두 작업이 어긋난 시작 때로 실제로 엇갈리나 · 작업 스케줄러가
띄운 claude 가 작업 묶음을 벗어나 사나 · 작업 스케줄러가 띄운 자리에서 통합 인증이 넘나 · 사람이 평소 Edge 에서 일하는 낮의 뒤 시각에 다시 로그인이 서고
그 보고가 끝까지 지어지나(사람이 곧 다시 로그인하면 이쪽 세션이 도중에 끊긴다) · 스스로 로그인이 진짜 입구 · 진짜 통합 인증으로 서나(입구는
대역이다 — 입구의 사람 없는 꼴은 스킬 ep-login 의 검사가 가짜 SSO 로 잰다) · 진짜 돌려주는 문이 평소 Edge 의 포털을 살리고 쓰지 않는 EP 탭만 닫나(대역이다 — 그 문은 스킬 ep-login 의 검사가 잰다) · 보고 창의 단추가 돌려준 뒤 빌려 넣고 곧 돌려주는 길(`presses.Borrow` → `clock.py lend · release`)은 판으로 안 재고 `loan` 을 함수로 한 번 확인했다 · 진짜 claude 가 그 권한으로 보고를 짓나(대역이 받은 명령줄 · 권한 · 부탁
글까지만 잰다 — 권한 규칙이 claude 안에서 어떻게 맞나, 업무 파악의 쓰는 손을 heredoc 째 부르는 꼴이 열리나는 진짜 claude 에 띄워 확인할 몫이고, 막은
목록은 여기서 그 꼴의 글자 맞추기로 견준다) · 맡긴 일(`handed.py` — 영구 판정이 없다. 창의 검사는 `handed.py` 입구를 대역으로 받는다) · 자리 밖에서 보기의
보내기 가운데 위 판정 밖의 갈래(넘기기 전 거절은 다음 판에 · 도중 끊김과 남은 「보내는 중」은 다시 안 보냄 · 안 켠 PC 와 대화의 보고는 안 보냄 — 가짜
중계에 대고 한 번 쟀고 판정으로 두지 않는다) · 진짜 사내 중계가 본인 사본을 받은편지함에 세우나 · 휴대폰 메일에서 그 꼴로 서나(회사 판).
