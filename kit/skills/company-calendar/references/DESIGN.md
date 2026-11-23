# 일정 손의 짜임 — 막는 까닭 · 바꾸는 손의 경계 · 손가락의 표

`scripts/company_calendar.py`(명령)와 일정 손 — 들머리 `scripts/agenda.py` 와 그 몸인 `agenda_shapes.py` · `agenda_rows.py` · `agenda_reader.py` · `agenda_changes.py`(무엇이 어디 사는지는 아래 「조각의 지도」) — 를 고치기 전에 읽는다. 부르는 꼴 · 내는 것은 그 파일 머리말과 `--help` 의 지도가,
일정 앱의 주소와 꼴은 `SOURCES.md` 「사내 일정 앱에서 잰 것」이 든다.

## 명령의 손가락은 표다

얇은 명령(`company_calendar.py`)의 할 수 있는 것은 표 넷이 든다 — 출발(`STARTS`) · 바꿀 것(`CHANGES`) · 끝(`ENDS`) · 읽기(`READS`).
인자 · 「이 출발에 없는 손가락」 거절과 그 일을 어디서 하는지 · `--help` 의 지도가 다 이 표에서 선다. 출발 「내 일정 한 건」의 끝은
고치기 · 지우기 둘이다 — 고치기는 제목 · 장소 · 시각만 받고(설명 · 비공개 · 하루 종일 · 중요는 넣을 때만), 지우기는 바꿀 것을 안 받는다.
거름은 손가락을 끝보다 먼저 본다 — 그 출발이 안 받는 칸을 준 부름은 「그 끝으로」가 아니라 그 일을 어디서 하나를 받는다.
표 밖의 명령은 둘이다 — 일정 앱 주소를 남기는 `remember` 와, 일정을 안 바꾸고 Teams 회의 예약 창을 띄우는 `teams-meeting`(아래 절).

표의 칸(출발 · 바꿀 것 · 아직 없는 손가락)과 그 칸만 보는 거름 · 지도 줄 · 열쇠의 해시는 회의실 손과 한 벌이라 형제 스킬 ep-login 의
`ep_command.py` 「손가락의 표」에 산다. 끝(`End`)과 거르는 차례는 손마다 제 것이다 — 일정의 끝은 「미리 보기의 key 를 받나」를, 회의실의
끝은 「바꿀 것을 받나」를 들어 같은 낱말이 다른 뜻이고, 그 뜻을 따라 거르는 차례도 갈린다. 답 크기에 맞춰 덜어 내는 셈(`fit_days`)도 겉만
닮았다 — 일정은 두 목록을 날 차례로, 회의실은 한 목록을 무리 차례로 덜어 하나로 묶으면 둘 중 하나의 차례가 틀어진다.

회사에서 안 잰 화면 동작과 안 짓는 것은 아직 없는 손가락의 표(`NOT_YET`)에 까닭과 함께 둔다. 모델이 짐작해 줄 만한 인자(`--repeat` ·
`--remind` · `--to` · `--who`)는 받아 두었다가 세션 전에 사람이 어디서 하나를 대며 멈춘다 — argparse 의 「모르는 인자」는 어디서 하나를
못 대고, 인자를 받기만 하고 안 보면 「반복으로」가 한 번짜리로 말없이 들어간다. 날 · 시각의 꼴도 세션 전에 본다.

한 번 부름은 일정 한 건을 한 번 다루는 것(사람이 화면 하나를 열어 칸을 바꾸고 단추 하나를 누르는 것)과 같은 크기다.

| 사람이 일정 화면에서 | 모델의 부름 | 한 부름에 묶은 것과 그 까닭 |
|---|---|---|
| 날 · 주 보기에서 내 일정함과 남의 공유 일정함을 함께 켠다 | `show [--who 이름 …]` 한 번 | 내 일정함 전부와 고른 공유 일정함을 한 답에 — 부름 둘로 나누지 않는다 |
| 함께 켠 일정함들에서 모두 빈 칸을 눈으로 찾는다 | `show --who 이름 … --free 분` 한 번 | 빈 칸 셈까지 손이 한다 — 줄을 받아 모델이 셈하면 하루 종일 · 여러 날 · 비공개 줄을 저마다 다르게 센다 |
| 주소록에서 찾은 사람들의 일정함을 하나씩 켠다 | `show --people-file people.json --free 분` 한 번 | 다른 손이 낸 사람을 그대로 받는다 — 이름을 일정함 이름으로 옮겨 적으면 동명이인이 남의 일정함으로 간다 |
| 빠른 등록 → 제목 · 시각 · 장소 · 설명 · 공개 범위 · 하루 종일 → [저장] | `preview` + `add` | 칸 아무 조합을 한 부름에 — 나눠 넣으면 공개 일정이 덜 된 꼴로 먼저 서고, 비공개는 넣은 뒤 고칠 손이 없다 |
| 일정 미리 보기 → 제목 · 장소 고침 → [저장], 일정을 끌어 옮긴다 | `preview --handle` + `edit` | 제목 · 장소 · 시각을 한 부름에 — 화면은 둘(저장 · 끌기)이지만 사람에게는 「그 일정을 이렇게」 한 말이라 한 열쇠로 묶는다 |
| 일정을 눌러 미리 보기를 연다 | `event <id>` | 장소 · 설명 · 참석자 · 응답 · Teams 링크를 한 답에 |
| 상세검색 · 검색 칸 | `find` | 칸 조건은 다 함께 · 본문 낱말은 홀로 — 화면과 같은 두 갈래. 찾기 화면이 안 보는 Teams 일정함(회의실 예약)은 겹침을 볼 때 읽는 일정 목록 한 번을 제목으로 거른다 — 그 줄에 장소 · 설명 · 참석자가 안 와 그 조건이 들면 안 본다고 답이 말한다 |
| 일정 → [삭제] → 확인 | (`show`) + `delete --handle` | `show` 의 줄이 곧 사람이 본 판이고 `handle` 이 그 지문이라 지우기 앞에 미리 보기를 따로 안 부른다 |

열쇠 — `preview` 와 `add` 는 같은 판(`plan_new`)을 짓고 그 판 전체(보인 값 · 내 일정함 전부의 겹침 · 이미 있나)의 해시가 key 다.
`add` 는 판을 다시 지어 key 가 다르면 `moved` 로 안 넣는다 — 모델이 보인 값과 다른 값을 넘겨도 손이 막는다. 손(agenda)의 끝
낱말(`clashed` · `changed`)은 명령에서 「보인 판과 다르다」 하나(`moved`)로 모은다 — 형제 스킬 company-meeting-room 과 낱말 하나가 뜻
하나다.

함께 고른 여러 건 — 사람이 한 확인에서 여러 건을 고르면, 앞 건을 넣는 순간 그와 겹치는 뒤 건의 판(겹침)이 바뀌어 `moved` 로 돈다.
길은 셋이었다: 여러 건을 한 판 · 한 열쇠로 묶기, 방금 넣은 건을 열쇠에서 빼 주기, 「한 번에 하나씩 보이고 넣기」. 묶기는 보고 창의 카드처럼
한 건씩 누르는 확인에는 못 쓰는 둘째 확인 꼴이 되고, 빼 주기는 사람이 뒤 건을 보며 앞 건과의 겹침을 본 적이 없는데도 넣어 「사람이 본 판과
들어가는 판이 같다」를 깬다. 그래서 겹침 쪽을 넓힌다 — 뒤 건의 `preview` · `add` 에 앞 건을 `--alongside` 로 주면 앞 건이 겹침에
「planned」 한 줄로 서서 사람이 확인 때 그 겹침을 보고, 앞 건이 먼저 들어 일정에 서도(제목 · 시작 · 끝이 같은 줄만 — `landed_of`) 판이
그대로다. 그 밖의 새 일정은 여전히 `moved` 다. 이 인자가 없는 부름(보고 창의 카드 한 건)은 판이 예전과 같아, 같은 시각의 카드 둘을 잇달아
누르면 뒤 것이 안 들고 그렇다고 말하는 끝도 그대로다.

기한 알림 — `preview --due` 가 알림 자리를 찾아 그 시각의 판을 짓는다. `add` 는 답의 `start` · `end` 를 그대로 받아 같은 판을 다시 짓는다 —
`add` 가 자리를 다시 찾으면 그 사이 앞 알림이 들었나에 따라 자리가 달라져 열쇠가 어긋난다. 같은 날 둘째 알림은 첫째를 `--alongside` 로 받아
그 자리를 피하고, 둘은 안 겹쳐 서로의 판에 안 서므로 어느 쪽을 먼저 넣어도 · 하나만 넣어도 열쇠가 맞는다. 하루 종일로 넣지 않는다 — 하루
종일 줄은 다 비는 때의 셈(`busy_of`)에서 그날을 통째로 막는다. 길이 · 구간은 `REMINDER_MINUTES` · `WORK_HOURS` 한 자리다.

## 모두 비는 때 — 줄이 드는 것만으로 센다

`show --free` 는 읽은 일정함 전부(내 기본 · Teams · `--who` · `--shared`)의 바쁜 때를 빼고 평일마다 근무 구간(`WORK_HOURS` · `--hours`)
안에서 그 분 이상 남는 틈을 낸다. 틈 셈은 형제 스킬 ep-login 의 `ep_command.gaps_of` 하나를 회의실 손과 함께 쓴다. 줄마다 어떻게
세나는 `busy_of` 가 정하고, 줄이 실제로 드는 것만 쓴다(`SOURCES.md`).

- 시각이 온 줄은 그 시각대로 바쁘다 — 참석 답 전 초대 · Teams 줄 · 남이 비공개로 든 줄(제목 · 시각이 그대로 온다)도 같다
- 하루 종일 · 여러 날 줄의 꼴은 안 쟀다 — 그날(들) · 시작부터 끝까지 내내 바쁜 것으로 센다. 비는 때를 지어내면 회의실 예약과 참석자
  안내라는 되돌릴 수 없는 걸음으로 이어지니, 틀려도 「안 빈다」 쪽으로 틀리게 둔다. 그 줄은 `assumed` 에 까닭과 함께 달려 사람이
  바로잡는다
- 끝이 시작과 같은 줄은 길이를 몰라 안 세고 `assumed` 에 단다. 시각을 못 읽은 줄은 손(agenda)이 버리며 `Reader.unread` 에 세고,
  못 읽은 일정함은 `shared_failed` 에 선다 — 셋 다 `word` 가 사람에게 말하라 이른다. 어느 것도 말없이 「빈다」로 넘어가지 않는다
- 사람 파일의 사람은 Notes 이름으로만 일정함에 잇는다(`people_books` — 공유 일정함 줄의 일정함을 가진 사람). 공유받지 않은 사람 ·
  Notes 이름이 빈 사람은 `unseen` 에 까닭과 함께 서고 `word` 가 그분은 비는지 모른다고 말하라 이른다 — 공유하지 않은 일정함의 빈
  때를 보는 길은 회사에서 안 쟀다(`SOURCES.md` 「회사에서 잴 것」)
- 오늘의 틈은 지금 뒤 첫 눈금(`SLOT_STEP_MINUTES`)부터다 — 분 · 초가 잘린 시작은 회의실 손이 「지난 시각」으로 막는다
- 공휴일(일정 앱의 공용 일정 DB)은 주말처럼 뺀다 — 일정 화면이 달력에 붉게 보이는 그 목록이다. 못 읽으면 빼지 않고 `word` 가 「공휴일을
  못 뺐다」고 이른다. 하루짜리 하루 종일 줄은 그날 내내 바쁘다(꼴을 쟀다) — 여러 날 하루 종일 줄만 짐작으로 단다

## Teams 회의 예약 창 — 링크 하나를 짓고 열 뿐이다

`teams-meeting` 은 Microsoft 가 문서로 든 회의 예약 딥 링크(`SOURCES.md` 「Teams 회의 예약 창」)를 받은 칸으로 짓고 등록된 https 처리기로
연다. 회사 일정 앱 · 세션에 안 닿고, 회의를 잡지도 않는다 — 회의가 서고 초대가 가는 것은 사람이 Teams 창에서 [보내기]를 누를 때다. 그래서
미리 보기 → 열쇠의 짝이 없다: 사람이 보내기 전의 창이 곧 미리 보기이고, 마지막 단추는 사람의 것이다. 메일 손이 임시메일을 Edge 에 띄워 두는
것과 같은 꼴이다.

- 손은 고르지 않는다 — 영상 회의로 할지 · 누구 · 언제는 모델이 정해(주소록의 사람 파일 · `show --free`) 넘긴다. 손이 거절하는 것은 링크로
  안 서는 것뿐이다: 시작 없는 끝 · 시작보다 앞이거나 같은 끝 · 메일 주소 꼴이 아닌 참석자 · 사람 파일에서 주소가 빈 사람 · Teams 가 넘겨받지
  못하는 길이. 주소 없는 분을 빼고 열면 사람이 모르는 채 그분이 빠진다
- 인코딩 — 값은 다 퍼센트 인코딩한다. 빈칸이 `+` 면 Teams 가 빈칸으로 안 읽고, 시각의 `+09:00` 이 날로 가면 빈칸으로 읽혀 시간대가 깨진다.
  참석자의 `@` 와 이음표 쉼표는 문서의 꼴대로 날로 둔다
- 길이 — 한도는 손이 지은 링크가 아니라 teams.microsoft.com 이 그 링크를 한 번 더 인코딩해 넘기는 주소에 걸린다(`teams_relayed` 가 그 셈을
  짓는다). 넘으면 Teams 가 창 대신 404 를 내니 안 열고, 설명부터 줄이라는 말과 함께 멈춘다. 한글 설명이 가장 먼저 넘친다
- 보낸 회의는 Teams 일정에 서고 회사 일정 화면에도 보인다 — 일정에 또 넣으면 같은 회의가 둘이다. 회의실이 드는 회의는 회의실 예약이 Teams
  링크를 만들어 이 창과 함께 쓰면 회의가 둘이다
- 사람 없는 아침 보고는 이 명령을 못 부른다 — 사람의 화면이 바뀌는 일이라 스킬 mailbox-scan 의 막는 명령에 바꾸는 명령들과 함께 든다
- 시험장은 `TEAMS_LINK_SINK` 를 채워 창 대신 그 파일에 연 주소를 적게 한다 — 답은 진짜 길과 같은 「열었다」에 「(가짜 회사 — 창 없음)」만
  단다(메일 손의 임시메일 띄우기 대역과 같은 꼴). 「안 열었다」고 하면 `state: opened` 와 어긋나 부른 쪽이 들었는지 모른다고 읽는다

## 읽는 손은 닫힌 목록으로 막는다

읽는 손(`Reader`)은 안 바꾸는 것을 잰 주소만 묻는다 — 일정함 목록(`agGetCalendar`) · 내 일정(`getcalendareventMe`) · 공유받은
일정함의 일정(그 일정함의 서버 · DB 의 `getcalendarevent`) · 한 건 미리 보기(`vweventprev/<unid>?opendocument`) · 상세검색 · 본문 찾기 ·
공휴일(같은 서버 공용 DB 의 `vwHolidays`). 이 앱에서는 「GET 은 안 바꾼다」가 안 선다 — 일정 줄의 `url` 은 편집
화면(`?editdocument`)이고 지우기도 GET 이다. 그래서 막기는 닫힌 목록이고, 그 밖의 주소는 서버에 닿기 전에 `ChangeRefused` 로 막는다.
새 주소는 안 바꾸는 것을 잰 뒤 목록에 더해야 묻는다. 사내 도메인 밖 서버는 묻지 않는다 — 세션 쿠키를 밖에 안 싣는다.

## 일정을 바꾸는 손 셋 — 언제 부르나는 부르는 쪽이 정한다

일정을 바꾸는 손은 넣기(`register`) · 고치기(`edit`) · 지우기(`delete`) 셋뿐이고 이름 붙은 함수 하나씩이다. 둘 다 서버의 답이 성공을 못 가려서,
끝은 다시 읽은 일정이 정한다. 저장 · 지우기 요청이 도중에 끊겨도 다시 읽어 가린다.

- 넣기는 참석자 · 참조 칸을 비워 남에게 알림이 안 가고, 같은 일정(제목 · 시작 · 끝)이 이미 있으면 넣지 않는다. 확인에 보인
  겹침(`shown_clash`) 밖의 일정이 그 시각에 새로 들었으면 넣지 않는다 — 사람은 그 겹침을 모르고 「네」 했다. 겹침은 확인이 본 자리와
  같은 자리, 곧 내 일정함 전부(기본 · Teams)에서 다시 센다 — 기본 일정함만 세면 Teams 에 새로 든 회의를 모른 채 넣는다
- 지우기는 쓰는 사람이 손수 든 단건(`Event.keep_reason` 이 빈 줄)만, 화면이 보인 그 줄이 그대로일 때 지운다. 그 줄이 옮겨졌거나
  제목 · 시작 · 끝이 보인 것과 다르면 안 지운다. 응답 칸이 찬 내 일정은 한 건 읽기로 참석자 · 참조자를 보고, 들었으면 안 지운다
- 고치기는 지우기와 같은 경계에 하나를 더한다 — 한 건 읽기에 참석자 · 참조자가 들면 안 고친다(고치면 일정 앱이 그분들께 알림을
  권한다). 하루 종일 줄의 시각은 안 옮긴다. 끝은 다시 읽은 줄의 제목 · 시각과 한 건 읽기의 장소가 정한다

`register` · `delete` 는 남이 보는 회사 일정을 바꾸고, 지운 일정은 되돌릴 손이 없다. 사람이 그 한 건을 두고 「넣는다 · 지운다」를
분명히 고른 뒤에만 부른다 — 회차 · 예약 작업 · 모델의 판단이 스스로 부르지 않는다. 이 파일은 그 확인을 대신하지 않는다.

## 지우지 않는 줄

`Event.keep_reason` 이 까닭을 든다.

- 받은 초대(줄의 `attOwner` 가 남)는 남이 연 회의에 든 자리라 지우기가 곧 참석 답이다 — 응답 칸으로 가르지 않는다: 내가 든 일정도
  미리 보기 [저장] 뒤 `accepted` 가 선다. 그 칸이 없는 줄만 응답 칸으로 가른다
- 회의 줄은 쓰는 사람이 연 회의여도 지우면 참석하실 분께 알림이 갈 수 있다
- 반복 일정은 지우기를 안 쟀다(하루 종일 단건은 쟀다 · 지운다)
- 쓰는 사람이 고칠 수 있는 줄이 아니면(줄의 `editors` 에 그 사람이 안 든다) 안 지운다
- 공유받은 일정함은 읽기만 한다 — 그 줄은 `keep_reason` 이 `shared` 이고, 그 줄(`Event`)이나 `Seen.of` 로 지은 손잡이를 지우기에
  주면 묻기 전에 `ChangeRefused`(`reason` 은 `shared`)다. 글줄 손잡이(`Seen.parse`)는 그 표지를 잃는다

남의 일정(공유받지 않은 것) · 회의실 · 참석 답은 이 파일에 없다.

## 검사 — 설정 저장소의 `_check/skills/company-calendar/check_agenda.py` 의 가짜 일정 앱이 지키는 꼴

- 쿠키가 없거나 세션이 끊긴 판이면 200 에 SSO 로 보내는 HTML
- 일정은 두 배열(반복은 날짜마다 한 줄 · 단건)이고 제목은 HTML 엔티티로 낸다
- 등록 화면의 폼은 잰 「값이 찬 칸」과 빈 칸을 숨은 칸으로 낸다 — 고정 값 칸의 실물 값은 안 쟀고 지어낸 값이다. 저장은 폼이 낸
  고정 값이 그대로 돌아와야 서고, 답은 늘 창 닫기다
- 참석자 칸이 찬 저장은 「남에게 알림이 갔다」로, 편집 화면 · 지우기 주소를 부른 것은 바꾼 요청으로 남긴다
- 공유 일정함 · Teams 일정함의 고정 줄은 판이 고른 날에 선다 — 모두 비는 때의 판은 지난 시각에 안 잘리는 앞날을 쓴다

남기는 까닭의 길 — 일정 줄마다 편집 주소가 실려 오고, 대화하는 모델이 이 손을 부르며, 이 파일을 그 자리에서 쓰는 앱이 있다.

## 조각의 지도

명령 `company_calendar.py` 는 손가락의 표(위 「명령의 손가락은 표다」)와 그 표를 엮는 손들이다. 일정 손은 바탕 → 글 꼴 풀기 → 읽는 손 →
바꾸는 손으로 아래에서 위 한쪽으로 싣고, 들머리 `agenda.py` 가 그 이름을 다 다시 내어 명령은 `agenda` 하나로 부른다(나무에서는 그 이름이
사는 모듈로 선다). 아래는 코드에서 뽑은 지도다 — 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고 다시 짓는다.
읽는 손의 메서드는 인스턴스(`reader.between()`)로 불려 나무에 이어지지 않고 클래스 `Reader` 아래에 선다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `company_calendar.py` · 입구 | 회사 일정 스킬의 얇은 명령 — 곁의 일정 손(``agenda.py``)을 불러 보기 · 넣기 · 지우기를 한다. | `agenda` | ep-login 의 `ep_command` · `ep_session` |
| `agenda.py` | 사내 일정 앱(HCL Domino 웹 일정)의 내 일정함을 읽는 손과, 일정을 바꾸는 이름 붙은 손 셋(``register`` · ``edit`` · ``delete``) — 표준 라이브러리와 형제 스킬 ep-login 의 ``ep_session``(세션 파일 → 쿠키 통, 스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)만 쓴다. | `agenda_changes` · `agenda_reader` · `agenda_rows` · `agenda_shapes` | — |
| `agenda_changes.py` | 일정을 바꾸는 이름 붙은 손 셋(``register`` · ``edit`` · ``delete``)과 그 손가락. 바깥: 일정 앱(망) — 읽는 손의 세션을 쓴다. | `agenda_reader` · `agenda_rows` · `agenda_shapes` | — |
| `agenda_reader.py` | 일정함을 읽는 손 — 읽기 전용으로 잰 주소만 묻는다. | `agenda_rows` · `agenda_shapes` | — |
| `agenda_rows.py` | 일정 앱의 글 꼴을 일정 손의 꼴로 푼다 — JSONP 몸통 · 일정 줄 · 한 건 문서 · 등록 화면의 폼. 바깥에 닿지 않는다. | `agenda_shapes` | — |
| `agenda_shapes.py` | 일정 손의 바탕 — 이름 붙은 값 · 예외 · 시각 · 꼴(일정함 · 일정 줄 · 넣을 것 · 손잡이 · 한 건 · 끝)과 시각 말. 바깥에 닿지 않는다. | — | ep-login 의 `ep_command` · `ep_session` |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 입구 — 인자를 읽고 일정 손을 실어 ``work`` 의 답을 JSON 하나로 찍는다(종료 값은 ``ep_command.finish``).
  - `parser` — 명령의 인자 표 — 하위 명령과 인자를 표 넷(``STARTS`` · ``CHANGES`` · ``ENDS`` · ``READS``)에서 세우고, 머리 · 지도 · 종료 값 범례를 --help 에 단다.
    - `common_steps` — 맨 위 --help 의 머리 — 자주 쓰는 길을 그대로 칠 수 있는 꼴로, 그리고 오늘과 날짜 표. 요일로 말한 날을 모델이 고르는 자리다.
    - `finger_map` — --help 의 지도 — 표 넷에서 짓는다.
      - `End` — 끝 하나 — 누르는 단추. 다 회사 일정을 바꾼다.
    - ↑ `End`
  - `work` — 명령 하나 — teams-meeting 은 세션 없이 창을 띄우고, 나머지는 세션 앞 거름을 지난 뒤 세션을 쥐고 판을 돈다.
    - `teams_meeting` — teams-meeting 의 답 — 링크를 짓고 연다.
      - `teams_link` — Teams 회의 예약 창의 주소와 채운 칸(답의 ``form``) — 받은 칸만 싣고 무엇도 고르지 않는다.
        - `teams_times` — 창에 채울 (시작, 끝) — 서울 벽시계(``stamp_of``). 끝만 있거나 끝이 시작보다 앞이거나 같으면 Stop(인자).
        - `teams_attendees` — 참석자 메일 주소 — --to(빈칸 · 쉼표로 여럿)와 사람 파일(사람마다 그 email)을 준 차례대로, 같은 주소는 한 번. 주소 꼴이 아닌 것과 주소가 없는 사람 파일의 사람은 Stop(인자) — 빼고 열면 사람이 모르는 채 그분이 빠진다.
        - `teams_form` — 답의 ``form`` — 채운 칸만(제목은 한 줄로 · 날과 요일 · 시각 말 · 설명 · 참석자).
          - `weekday_of` — 날 하나의 요일 한 글자(「월」 … 「일」).
          - `agenda_shapes.clock_span` — 두 시각의 서울 벽시계 「HH:MM–HH:MM」.
        - `teams_query` — Teams 딥 링크 — 값은 퍼센트 인코딩한다(빈칸은 ``%20`` — Teams 는 ``+`` 를 빈칸으로 안 받고, 시각의 ``+09:00`` 은 ``%2B`` 여야 산다). 시각은 서울 벽시계를 시간대가 붙은 ISO 8601 로 옮긴다.
        - `teams_relayed` — teams.microsoft.com 이 이 링크를 받아 넘기는 주소의 길이 — 그쪽이 경로부터의 글을 한 번 더 인코딩해 시작 화면 주소에 싣는다.
      - `open_teams` — 링크를 연다 — 등록된 https 처리기(기본 브라우저)가 받고, Teams 가 제 앱이나 웹에 예약 창을 띄운다.
      - `teams_word` — Teams 창을 연 말 — 어디에 열었나 · 보내기는 사람 · 안 채운 칸.
    - `find_span` — 찾기의 인자 — 본문 낱말(--text)이면 None, 칸 조건이면 (첫날, 끝날). 세션 없이 가린다 — 섞인 조건 · 빈 조건 · 틀린 날 · 거꾸로 선 기간은 Stop(인자).
    - `guard_change` — 넣기 · 고치기 · 지우기의 세션 앞 거름 — 표에 없는 손가락 · 빠진 값(``fingers``)과 날 · 시각 · 손잡이 · 함께 넣는 건의 꼴. 넣기 · 고치기는 손부터 받는 길이라 세션을 받기 전에 멈춘다.
      - `fingers` — 부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 손가락 · 설 수 없는 기한 알림 · 출발에 없는 끝 · 빠진 값 · 끝에 안 맞는 바꿀 것의 수를 차례로 거른다(저마다 그 일을 어디서 하는지 대며 Stop(인자)). 출발을 낸다.
        - `refuse_due` — 기한 알림(``--due``)이 설 수 없는 부름이면 Stop(인자) — preview 가 아니거나, 손이 찾을 시각(--start · --end · --all-day)을 함께 주었다.
        - `end_of` — 부른 명령이 맺는 끝 — preview 는 그 출발의 끝 가운데 확인(``--confirm``)을 받는 것이다.
          - ↑ `End`
        - `due_fills` — 빠진 값을 거를 때 기한 알림이 채운 손가락을 가리는 물음(줄 → 참 · 거짓) — ``--due`` 를 받았으면 시작 · 끝은 손이 찾아 빠진 값이 아니다.
        - `refuse_change_count` — 바꿀 것의 수가 그 끝에 안 맞으면 Stop(인자) — 바꿀 것을 안 받는 끝(지우기)에 주었거나, 있던 일정을 고치는데 하나도 안 주었다.
          - ↑ `End`
      - `due_of` — --due 의 (날, 마감 시각이나 None) — 「<날> HH:MM」 이면 시각이 있는 기한, 날만이면 없는 기한. 꼴이 아니면 Stop(인자) — 세션 전에 가린다.
      - `want_of` — 넣을 일정 한 건을 인자에서 짓는다 — 하루 종일이면 날을 그 날들의 구간으로, 회사 일정에 남는 꼴로 다듬고 못 넣는 값이면 Stop(인자).
        - `agenda_shapes.whole_days` — 하루 종일 일정의 (시작, 끝) — 첫날 서울 0 시부터 끝날 다음 날 0 시까지(UTC).
          - `CalendarConfigError` — 주소 · 쿠키 파일 · 인자가 틀렸다 — 묻기 전에 잡힌다.
        - `whole_day_of` — 하루 종일의 첫날 · 끝날 — 날 말 · 요일 말 · YYYY-MM-DD(``day_of``).
        - `agenda_shapes.kst` — 서울 벽시계 ``YYYY-MM-DD HH:MM`` → 시간대가 붙은 UTC. 꼴이 아니면 ``CalendarConfigError`` — 말은 ``ep_command.stamp_of`` 의 것이다.
          - ↑ `CalendarConfigError`
        - `agenda_shapes.Want` — 회사 일정에 넣을 한 건 — 시각은 시간대가 붙은 것만(``kst`` 로 짓는다). ``note`` 는 설명 칸이다.
          - `Want.day` — 넣을 일정이 시작하는 서울 날짜.
            - `kst_day` — 시각의 서울 날짜.
              - `_aware` — 시간대가 붙은 시각만 받는다 — 없으면 CalendarConfigError.
                - ↑ `CalendarConfigError`
          - `Want.last_day` — 그 일정이 드는 마지막 서울 날짜 — 하루 종일이면 끝(다음 날 0 시)의 앞날이다.
            - ↑ `kst_day`
          - `Want.cleaned` — 회사 일정에 실제로 남는 꼴 — 보이지 않는 글자 · 줄바꿈을 걷고 상한에서 자른 제목 · 설명 · 장소. 확인에 이 꼴을 보인다.
            - `clean_title` — 제목 — 보이지 않는 글자 · 줄바꿈을 걷고 ``TITLE_MOST`` 에서 자른다.
              - `_clean` — 글을 회사 일정에 남는 꼴로 — 보이지 않는 글자를 걷고 빈칸을 하나로, ``most`` 에서 자른다.
            - `clean_note` — 설명 칸 — 제목과 같은 거름에 ``NOTE_MOST`` 상한.
              - ↑ `_clean`
            - ↑ `_clean`
        - `unfit_stop` — 값이 안 서는 까닭이 있으면 ``words`` 의 차례로 첫 까닭의 말을 Stop(인자)으로 — 다 서면 지나간다.
        - `agenda_changes.values_unfit` — 넣거나 고칠 값이 안 서는 까닭들 — 끝이 시작 뒤가 아님(``span`` 일 때만 본다 — 고치기는 시각을 옮길 때만) · 빈 제목. 넣기 · 고치기와 명령의 그 판이 이것 하나로 본다.
          - ↑ `agenda_shapes._aware`
      - `agenda_shapes.Seen` — 사람에게 보인 일정 한 줄의 손잡이 — 그 줄의 열쇠(``ref`` — 일정 열쇠 · 시작의 해시) · 그 일정의 열쇠(``ident`` — 일정 열쇠만의 해시 · 시각을 옮겨도 같다) · 제목 · 시작 · 끝의 지문(``mark``) · 서울 날짜(``day``). 일정 열쇠(사번이 든다)를 그대로 싣지 않는다.
        - `Seen.of` — 보인 일정 한 줄의 손잡이를 짓는다 — 그 줄의 열쇠 · 일정의 열쇠 · 지문 · 날.
          - `event_ref` — 일정 한 줄을 가리키는 열쇠 — 일정 열쇠(사번이 든다)의 해시.
            - `event_key` — 일정 한 줄의 날것 열쇠 — 일정 열쇠와 시작 시각(반복의 날마다 갈린다).
              - `_stamp` — 열쇠 · 지문에 싣는 시각 글자 — UTC ISO 8601(초까지). 같은 일정이면 늘 같은 글자다.
                - ↑ `_aware`
          - `event_ident` — 그 일정의 열쇠 — 일정 열쇠만의 해시. 같은 날 시각을 옮긴 줄을 「바뀜」으로 알아본다(반복의 날마다 같은 값이다).
          - `event_mark` — 보인 일정의 지문 — 제목 · 시작 · 끝. 지우기가 지금의 그 줄과 견준다(그사이 바뀌었으면 안 지운다).
            - ↑ `clean_title`
            - ↑ `_stamp`
        - `Seen.handle` — 손잡이를 대화를 건널 글 한 줄로 쓴다.
        - `Seen.parse` — 글 한 줄을 손잡이로 되읽는다 — 꼴이 아니면 CalendarConfigError.
          - ↑ `CalendarConfigError`
      - `change_of` — 고칠 칸(제목 · 장소 · 시작 · 끝)을 인자에서 짓는다 — 회사 일정에 남는 꼴로 다듬는다.
        - `agenda_shapes.Change` — 한 건 고치기에서 바꿀 것 — 안 바꾸는 칸은 None. 시각은 시간대가 붙은 것만.
          - `Change.cleaned` — 고칠 칸을 회사 일정에 남는 꼴로 — 준 칸만 다듬는다.
            - ↑ `clean_title`
            - ↑ `_clean`
          - `Change.moves` — 시각을 옮기는 고침인가 — 시작이나 끝을 준다.
        - ↑ `agenda_shapes.kst`
      - `alongs_of` — ``--alongside`` 들 — 「시작|끝|제목」(preview 답의 alongside 그대로). 꼴이 아니면 Stop(인자) — 세션 전에 가린다.
        - ↑ `agenda_shapes.clean_title`
        - `Along` — 같은 확인에서 사람이 함께 고른 다른 한 건(``--alongside``) — 겹침에 「planned」 로 서고, 그 건이 먼저 들어 일정에 서도 이 건의 판은 같다.
          - `Along.word` — 함께 고른 건을 ``--alongside`` 로 다시 줄 글 한 줄(시작 · 끝 · 제목).
      - ↑ `agenda_shapes.CalendarConfigError`
    - `guard_show` — show 의 세션 앞 거름 — 날 · ``--free`` · ``--hours`` · 사람 파일. 틀리면 Stop(인자).
      - `show_days` — show 의 첫날 · 끝날 — 첫날을 안 주면 오늘 · 내일, 첫날만 주면 그 하루. 꼴이 아니거나 끝날이 첫날보다 앞이면 Stop(인자).
      - `free_window` — show 의 --free · --hours — (하루의 처음, 끝) 이나 --free 가 없으면 None. 틀렸으면 Stop(인자).
        - `hours_of` — 「HH:MM-HH:MM」 → (처음, 끝) 시각 — 꼴이 아니거나 없는 시각이면 None. 앞뒤 차례는 안 본다.
    - `run` — 명령 하나의 판 — 일정 앱 주소를 고르고 그 명령의 손에 넘긴다.
      - `app_url` — 이 판의 일정 앱 주소(``…/<이름>.nsf`` 까지)와 그것이 잰 기본인가 — remember 는 받은 주소다.
        - `resolve` — 일정 앱 주소와 그것이 기본값인가 — ``--url`` → ``CALENDAR_URL`` → 남긴 주소 → 잰 기본(``agenda.DEFAULT_APP_URL``).
          - `saved_url` — 남긴 일정 앱 주소 — 파일이 없거나 꼴이 아니면 빈 글자.
            - `saved_place` — 남긴 일정 앱 주소 파일의 자리 — 읽기와 쓰기가 이것 하나로 찾는다.
      - `agenda_reader.Reader` — 일정함을 읽는 손 — 읽기 전용으로 잰 주소 셋만 묻는다.
        - ↑ `agenda_shapes.CalendarConfigError`
        - `agenda_shapes.SessionMissing` — 쿠키 파일이 없거나 쿠키가 하나도 없다 — 사내 세션을 먼저 받아 남긴다.
        - `read_only_shapes` — 읽는 손이 내 일정 DB(``db_path``)에 물을 수 있는 주소 꼴 — 닫힌 목록이라 새 꼴은 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다.
        - `public_view` — 공용 일정 DB 의 공휴일 보기 자리 — 내 일정 DB 와 같은 회사 코드(경로의 첫 마디) 아래다.
        - `Reader.from_env` — 환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES``(둘 다 꼭 준다 · 없으면 ``CalendarConfigError`` · ``SessionMissing``).
          - ↑ `agenda_shapes.CalendarConfigError`
        - `Reader.url` — 일정 앱 주소 — 서버와 DB 자리를 잇는다.
        - `Reader._get` — 읽기 GET — 앱 안의 ``path``. 일정을 바꾸는 주소 · 잰 꼴 밖의 주소는 묻지 않고 ``ChangeRefused``.
          - `agenda_shapes.ChangeRefused` — 읽는 손이 일정을 바꿀 주소(또는 읽기 전용으로 잰 꼴 밖의 주소)를 지었거나, 지우는 손이 지우지 않는 줄을 받았다 — 서버에 닿기 전에 막았다.
          - `Reader._open` — 막기 없는 요청 — 읽기는 ``_get`` · ``_get_shared`` 를 거쳐서만, 바꾸기는 ``register`` · ``delete`` 만 이것을 바로 부른다.
            - `agenda_shapes.SessionExpired` — 세션이 끊겼다 — 답 대신 SSO 화면이 왔거나 SSO 로 보냈다.
            - `agenda_shapes.CalendarError` — 일정을 못 읽었거나 못 바꿨다.
        - `Reader._get_public` — 공용 일정 DB(같은 서버 · 같은 회사 코드)의 공휴일 보기 한 꼴만 — 꼴 밖이면 묻지 않고 ``ChangeRefused``.
          - ↑ `agenda_shapes.ChangeRefused`
          - ↑ `Reader._open`
        - `Reader._get_shared` — 공유받은 일정함의 읽기 GET — 그 일정함의 서버 · DB 아래 잰 꼴 하나만. 꼴 밖이면 묻지 않고 ``ChangeRefused``.
          - ↑ `agenda_shapes.ChangeRefused`
          - ↑ `Reader._open`
        - `Reader._shared_server` — 공유 일정함 서버의 주소 — 읽는 손과 같은 호스트거나 같은 사내 도메인(첫 이름표를 뗀 나머지)의 호스트만. 세션 쿠키를 사내 밖으로 싣지 않으려는 문이다.
          - ↑ `agenda_shapes.CalendarError`
        - ↑ `Reader._open`
        - `Reader._text` — 답의 바이트를 글로 — 답이 댄 문자셋으로, 모르는 문자셋이면 UTF-8.
        - `Reader.calendars` — 일정함 목록 — JSON 배열(``text/html`` 로 온다). 내 것 · 공유받은 것이 다 든다.
          - ↑ `Reader._get`
          - ↑ `Reader._text`
          - ↑ `agenda_shapes.SessionExpired`
          - ↑ `agenda_shapes.CalendarError`
        - `Reader._mine` — 내 일정함 줄(``kind=PEO``) — 둘 이상이면 ``owner`` 가 다 같을 때만 선다(내 일정함이 기본 · Teams 둘인 사람). ``owner`` 가 다른 줄이 섞이면 ``CalendarError``(남의 일정함을 내 것으로 읽지 않게).
          - ↑ `Reader.calendars`
          - ↑ `agenda_shapes.CalendarError`
        - `Reader.book` — 내 기본 일정함 — 넣기 · 지우기가 가는 곳. ``kind=PEO`` 한 줄이면 그 줄이고, 여럿(같은 ``owner``)이면 ``calendartype=defaultCalendar`` 한 줄이다.
          - ↑ `Reader._mine`
          - ↑ `agenda_shapes.CalendarError`
          - `agenda_shapes.Book` — 일정함 하나 — 일정함 목록의 한 줄. 내 일정함(``kind=PEO``)은 ``owner`` 가 쓰는 사람의 Notes 이름(``CN=…/OU=…/OU=…/O=…``)이고 ``server`` · ``db_path`` 가 비었다(읽는 손의 주소를 쓴다). 공유받은 일정함(``GRW`` · ``GRR``)은 ``owner`` 가 그 일정함을 가진 사람의 Notes 이름 · ``name`` 이 목록에 뜨는 이름 · ``server`` · ``db_path`` 가 그 일정함이 든 자리(목록의 ``calhost`` · ``caldbpath``)다.
            - `Book.shared` — 공유받은 일정함인가 — 내 일정함의 갈래가 아니다.
        - `Reader.side_books` — 기본 일정함 밖의 내 일정함(Teams 따위 · 같은 ``owner``) — 읽기만 한다.
          - ↑ `Reader.book`
          - ↑ `Reader._mine`
          - ↑ `agenda_shapes.Book`
        - `Reader.mine_between` — 내 일정함 전부의 서울 날짜 ``first`` ~ ``last`` 일정 — 기본 일정함의 줄과, 기본 밖 일정함의 줄(``calendar`` 에 그 이름 · 지우는 손잡이는 없다)을 시작 차례로 한 목록에 낸다.
          - `Reader.between` — 서울 날짜 ``first`` ~ ``last``(둘 다 든다)에 걸친 일정 — ``book`` 이 없으면 내 일정함이다.
            - ↑ `agenda_shapes.CalendarConfigError`
            - `Reader.events` — ``start`` 부터 ``end`` 까지(앱이 받는 그대로)의 일정 — 반복(``data``) · 단건(``data2``) 두 배열을 다 받는다.
              - ↑ `Reader.book`
              - `agenda_rows._jsonp` — ``<CALLBACK>( … )`` 의 몸통 — 꼴이 아니면 끊긴 세션(SSO HTML 이 온다).
                - ↑ `agenda_shapes.SessionExpired`
                - ↑ `agenda_shapes.CalendarError`
              - ↑ `Reader._text`
              - `Reader._events_page` — 일정 목록 한 쪽 — 내 일정함은 읽는 손의 자리, 공유받은 일정함은 그 일정함의 서버 · DB 에서 잰 꼴 하나로 묻는다.
                - ↑ `Reader._get_shared`
                - ↑ `Reader._shared_server`
                - ↑ `Reader._get`
              - `agenda_rows.parse_rows` — 일정 줄들 — (읽은 줄, 시각을 못 읽거나 꼴이 아니어서 버린 줄 수). 차례는 받은 그대로다.
                - `parse_row` — 일정 줄 하나 — 시각을 못 읽으면 None(그 줄만 버린다). ``me`` 는 쓰는 사람의 Notes 이름(내 일정함의 ``owner``)이다.
                  - `_at` — 일정 줄의 시각 — ``YYYY-MM-DD HH:MM:SS``. 시간대 칸이 비면 서울, ``+HH:MM`` 이면 그 시간대.
                  - `agenda_shapes.Event` — 일정 한 줄. 반복 일정은 날짜마다 한 줄로 풀려 온다 — 같은 ``event_id`` 가 여러 날에 선다.
                    - `Event.day` — 일정이 시작하는 서울 날짜.
                      - ↑ `kst_day`
                    - `Event.keep_reason` — 지우지 않는 까닭 — 빈 글자면 지워도 된다(쓰는 사람이 손수 든 단건). 갈래마다의 까닭은 ``references/DESIGN.md`` 「지우지 않는 줄」이 든다.
                    - `Event.overlaps` — 일정이 ``start`` ~ ``end`` 에 겹치나.
                    - `Event.when` — 「10:00–11:00」 · 「하루 종일」 — 서울 시각.
                      - ↑ `clock_span`
                  - `_truthy` — 앱의 참 · 거짓 칸을 읽는다 — ``TRUE_WORDS`` 의 낱말이면 참.
                  - `_edits` — 쓰는 사람이 이 줄을 고칠 수 있나 — 앱의 ``editable`` 이 참이거나, 줄의 ``editors``(쉼표로 이은 Notes 이름)에 ``me`` 가 든다.
                    - ↑ `_truthy`
                  - `_invited` — 받은 초대인가 — 줄의 ``attOwner``(초대한 사람의 Notes 이름)가 차 있고 쓰는 사람이 아니면 참, 비었으면 거짓, 칸이 없거나 쓰는 사람을 모르면 None.
              - `distinct_events` — 같은 줄(``event_key`` — 일정 열쇠 · 시작)은 처음 것 하나만 — 반복 · 단건 두 배열에 같은 줄이 올 수 있다.
                - ↑ `agenda_shapes.Event`
                - ↑ `agenda_shapes.event_key`
              - `labelled` — 기본 밖 일정함 · 공유받은 일정함의 줄에 그 일정함 이름(``calendar``)을 단다 — 내 기본 일정함의 줄은 그대로.
                - `agenda_rows._person` — Notes 이름(``CN=이름/OU=…``)의 이름 — 꼴이 아니면 그대로.
              - `Reader._note_unread` — 시각을 못 읽어 버린 줄이 있으면 ``unread`` 에 (일정함 이름, 줄 수)를 쌓는다 — 부르는 쪽이 「안 보인 일정이 있다」를 알릴 길이다.
              - ↑ `agenda_rows._person`
          - `read_each` — 곁 일정함마다 ``read(일정함)`` 의 줄을 일정함 차례로 잇는다 — 끊긴 세션은 올리고, 못 읽은 일정함은 (일정함, 예외)로 모은다.
            - ↑ `agenda_shapes.Event`
            - ↑ `agenda_shapes.Book`
            - ↑ `agenda_shapes.CalendarError`
            - ↑ `agenda_shapes.SessionExpired`
          - ↑ `Reader.side_books`
        - `Reader.shared_books` — 공유받은 일정함 — 일정함 목록의 ``GRW`` · ``GRR`` 줄(목록 차례). 서버 · DB · 열쇠 · 일정함을 가진 사람이 빈 줄은 버린다.
          - ↑ `Reader.calendars`
          - ↑ `agenda_rows._person`
          - ↑ `agenda_shapes.Book`
        - ↑ `Reader.events`
        - ↑ `Reader._events_page`
        - ↑ `Reader._note_unread`
        - `Reader.detail` — 내 일정함의 일정 한 건 — 미리 보기 문서(``vweventprev/<unid>?opendocument``)의 장소 · 설명 · 참석자와 응답 · 참조자 · Teams 링크 · 고친 시각. 문서 보기라 안 바꾼다(편집 화면 ``?editdocument`` 은 짓지 않는다).
          - ↑ `agenda_shapes.CalendarConfigError`
          - ↑ `Reader._get`
          - `agenda_rows.parse_detail` — 미리 보기 문서의 칸 — 스크립트 ``EventDoc`` 의 칸과 칸 목록 표의 ``Subject`` · ``EventArea`` · ``Description``. ``EventDoc`` 가 없으면 끊긴 세션이다(SSO HTML 이 온다).
            - ↑ `agenda_shapes.SessionExpired`
            - `agenda_shapes.Detail` — 일정 한 건의 미리 보기 — 줄에 안 오는 칸. ``organizer`` 는 받은 초대면 연 사람(내가 든 일정이면 빈 글자).
              - `Detail.guests` — 참석자 · 참조자가 든다(또는 수 칸을 못 읽어 모른다) — 고치면 그분들께 알림이 갈 수 있다.
            - `_plain` — 문서 칸의 HTML 조각 → 글 — 줄바꿈 표시는 줄바꿈으로, 태그는 걷고 엔티티를 푼다.
            - `_people` — ``EventDoc`` 의 쉼표로 이은 칸들에서 사람들 — 이름 칸에 든 사람마다 한 줄. 칸 수가 이름 수와 다르면 그 칸은 비운다.
              - `agenda_shapes.Person` — 한 건 읽기의 참석자 · 참조자 한 사람 — 이름 · 메일 · 응답(``accepted`` · ``declined`` · ``tentative`` · ``needsAction``) · 한마디.
              - ↑ `_plain`
            - ↑ `_person`
          - ↑ `Reader._text`
        - `Reader.search` — 상세검색 — 기간(서울 날짜 · 둘 다 든다) 안에서 제목 · 장소 · 설명 · 참석자 이름에 그 글자가 든 일정(조건은 다 함께 걸린다). ⚠ 답의 줄은 끝이 시작과 같게 온다 — 끝 시각은 안 믿는다(부르는 쪽이 한 건 읽기 · show 로 본다).
          - ↑ `Reader.book`
          - `Reader._found` — 찾기의 답을 일정 줄로 푼다 — 못 읽은 줄 수를 적고 시작 차례로 세운다.
            - ↑ `agenda_rows._jsonp`
            - ↑ `Reader._text`
            - ↑ `agenda_rows.parse_rows`
            - ↑ `Reader._note_unread`
          - ↑ `Reader._get`
        - `Reader.search_text` — 본문 전체 찾기 — 제목 · 설명 · 장소 어디든 그 낱말이 든 일정(기간 없이 지난 해까지). 줄의 끝 시각이 온다.
          - ↑ `Reader.book`
          - ↑ `Reader._found`
          - ↑ `Reader._get`
        - ↑ `Reader._found`
        - `Reader.holidays` — 공휴일 — 서울 날짜 ``first`` ~ ``last``(둘 다 든다)의 {날: 이름}. 일정 앱의 공용 일정 DB(``vwHolidays``)가 든다.
          - ↑ `Reader._get_public`
          - ↑ `Reader._text`
          - ↑ `agenda_shapes.CalendarError`
        - ↑ `Reader.between`
      - `remember` — remember 의 답 — 이 주소로 내 일정함이 읽혀야 남긴다.
        - `book_unread` — 이 주소로 내 일정함이 안 읽히는 까닭(일정 앱 손의 예외) — 읽히면 None. 끊긴 세션은 올린다.
          - ↑ `agenda_shapes.SessionExpired`
          - ↑ `agenda_shapes.CalendarError`
        - `save_url` — 일정 앱 주소를 남긴다 — 남긴 자리를 낸다.
          - ↑ `saved_place`
      - `default_reads` — 잰 기본 주소가 이 사람의 일정함을 드나 — 다른 서버에 일정이 있는 사람이면 Stop(주소)으로 주소를 받게 한다.
        - ↑ `book_unread`
      - `calendars_of` — calendars 의 답 — 공유받은 일정함 목록.
      - `detail_of` — 일정 한 건의 답 — 줄에 안 오는 칸. 사람 칸은 이름 · 메일 · 응답 · 한마디.
      - `find_of` — 찾기 — 본문 낱말(--text) 이나 칸 조건(--title · --place · --note · --attendee · 기간). 내 기본 일정함과, 제목으로는 Teams 일정함(``side_found``)도.
        - ↑ `find_span`
        - `find_main` — 기본 일정함 찾기 — (걸린 줄, 어떻게 찾았나 ``text`` · ``fields``). 본문 낱말은 기간 없이, 칸 조건은 그 기간에서.
        - `side_found` — 찾기의 Teams 일정함 쪽 — 찾기 화면은 그 일정함을 안 찾아(회사에서 잼 · 0 건), show · preview 가 겹침을 볼 때 읽는 일정 목록을 기간째 읽고 제목으로 거른다.
          - ↑ `agenda_shapes.clean_title`
          - ↑ `agenda_reader.read_each`
        - `found_answer` — 찾기의 답 — 찾은 줄 · 줄 수 · 말, 못 읽은 일정함이 있으면 그 줄.
          - `failed_rows` — 못 읽은 곁 일정함 (이름, 까닭) 들을 답의 ``shared_failed`` 줄로.
        - `found_rows` — 찾은 줄 — 기본 일정함의 줄에 Teams 쪽의 새 줄을 더해 시작 차례로. 끝 시각은 그 줄에 끝이 올 때만 싣는다.
          - ↑ `agenda_shapes.event_key`
          - ↑ `weekday_of`
        - `find_word` — 찾기의 말 — 어떻게 찾았나(``text`` · ``fields``) · Teams 일정함을 어떻게 했나(``side_found`` 의 낱말 — 읽었으면 그 기간, 조건 때문에 안 읽었으면 그 까닭, 곁 일정함이 없으면 말이 없다) · 다음 걸음.
      - `show_of` — show 의 답 — 날 → 내 일정함 → 곁에 읽을 공유 일정함 → 공유 일정함 읽기 → 본 분 맺기 → 공휴일 → 비는 때 → 답 → 답 크기.
        - ↑ `show_days`
        - ↑ `free_window`
        - `picked_books` — 곁에 읽을 공유 일정함 — 이름(``--who``) · 전부(``--shared``) · 사람 파일(``people_books``). (일정함, 본 사람, 못 본 사람).
          - `shared_books` — 공유받은 일정함 — ``who`` 를 주면 이름에 그 글자 가운데 하나가 든 것만. 하나도 안 걸리는 글자가 있으면 인자가 틀린 것이다.
          - `people_books` — 사람 파일의 사람마다 그 사람의 일정함 — (곁에 읽을 공유 일정함, 본 사람, 못 본 사람). 사람은 Notes 이름으로만 일정함에 잇는다 — 공유 일정함 줄의 일정함을 가진 사람(``Book.owner``)이 그것이고, 이름은 동명이인이 갈라지지 않는다.
        - `read_shared` — 공유 일정함마다 읽는다 — (시작 차례의 줄, 읽은 일정함 이름, 못 읽은 일정함의 (이름, 까닭)). 한 일정함이 안 읽혀도 나머지는 보인다.
          - ↑ `agenda_shapes.CalendarError`
        - ↑ `failed_rows`
        - `counted_books` — 셈에 든 일정함의 이름 — 내 기본 일정함 · 읽힌 곁 일정함(못 읽은 것은 뺀다) · 읽힌 공유 일정함.
        - `settle_people` — 사람 파일의 본 분 · 못 본 분을 맺는다 — 일정함을 골랐어도 그 일정함을 못 읽은 분은 본 분이 아니다.
        - `holidays_of` — 공휴일 {날: 이름} 과 못 읽은 까닭 — 못 읽어도 보기는 선다(끊긴 세션은 올린다).
          - ↑ `agenda_shapes.CalendarError`
        - `free_of` — 읽은 일정함 전부가 ``minutes`` 분 이상 함께 비는 때 — 평일마다 ``hours`` 안에서, 지난 시각은 빼고. 바쁜 구간은 ``busy_of`` 가 정하고 틈은 ``ep_command.gaps_of`` 가 센다.
          - `busy_spans` — 줄마다의 바쁜 구간(``busy_of``)과 시각을 짐작한 줄 (줄, 구간, 까닭) — 셈에 넣을 것과 사람에게 달 것.
            - `busy_of` — 일정 줄 하나를 모두 비는 때의 셈에 어떻게 넣나 — (바쁜 구간이나 None, 시각을 짐작했으면 그 까닭). 줄이 실제로 드는 것만 쓴다(``references/SOURCES.md``): 시각이 온 줄은 그 시각대로 — 참석 답 전 초대 · Teams · 비공개로 든 남의 일정(제목 · 시각이 그대로 온다)도 바쁘다.
              - ↑ `agenda_shapes.kst_day`
          - `split_days` — 구간의 날을 가른다 — (주말 날 글자, 공휴일 줄, 비는 때를 찾을 평일).
            - `holiday_row` — 공휴일 하루를 답의 줄로 — 날 · 요일 · 이름. 보기의 공휴일과 모두 비는 때가 뺀 공휴일이 같은 꼴이다.
              - ↑ `weekday_of`
          - `windows_of` — 평일마다 하루의 구간 ``span`` — 지난 시각은 지금 뒤 첫 눈금(``next_step``)부터. 남는 구간이 없는 날은 뺀다.
            - `next_step` — ``t`` 뒤(같으면 그대로)의 첫 ``SLOT_STEP_MINUTES`` 눈금 — 초가 남으면 다음 분부터 센다.
          - `slots_in` — 구간들 안에서 바쁜 구간(``spans``)을 피해 ``need`` 이상 비는 (시작, 끝) — 틈은 ``ep_command.gaps_of`` 가 센다.
          - `hours_label` — 하루의 구간 「HH:MM–HH:MM」.
          - `slot_rows` — 비는 때 (시작, 끝) 들을 답의 줄로.
            - ↑ `weekday_of`
            - ↑ `agenda_shapes.clock_span`
          - `narrower_than_work` — 고른 구간이 근무 구간(``WORK_SPAN``)보다 좁은가 — 좁으면 곁의 비는 때를 더 볼 자리가 있다.
            - ↑ `hours_of`
          - ↑ `hours_of`
          - `assumed_rows` — 시각을 짐작한 줄 가운데 찾은 구간에 닿는 것만 — 답의 줄과 까닭.
            - `row` — 사람에게 보일 일정 한 줄 — 날 · 요일 · 때 · 제목 · 지우기 손잡이 · 지우지 않는 까닭, 그 일정이 든 칸만 더한다.
              - ↑ `weekday_of`
              - ↑ `agenda_shapes.Seen`
              - `room_booking` — 회의실 예약 앱이 저절로 넣은 줄인가 — 제목이 ``ROOM_BOOKING`` 머리로 선다.
          - `free_word` — 모두 비는 때의 말 — 셈의 칸마다 한 문장(비는 때 · 곁 · 공휴일 · 공휴일 못 읽음 · 못 읽은 일정함 · 못 본 분 · 못 읽은 줄 · 짐작한 줄)과 다음 걸음. 셈하지 않는다.
            - `unseen_word` — 일정함을 못 본 사람들을 사람에게 할 말 하나로 — 동명이인이 갈리게 부서를 붙인다.
        - `show_answer` — show 의 답 — 칸의 차례대로: 오늘과 구간 · 내 일정 줄 · 줄의 말, 곁에 청했으면 공유 일정 줄(``shared`` 가 None 이 아니면 비어도 싣는다) · 사람 파일을 주었으면 본 분, 그리고 있는 것만 못 읽은 일정함 · 못 읽은 줄 · 공휴일 · 공휴일을 못 읽은 까닭 · 비는 때.
          - ↑ `weekday_of`
          - ↑ `row`
          - `shared_row` — 공유받은 일정함의 일정 한 줄 — 내 줄의 꼴에서 비공개를 더하고 참석 답 · 한 건 읽기 열쇠를 뺀다.
            - ↑ `row`
          - `unread_rows` — 시각을 못 읽어 뺀 줄 (일정함 이름, 줄 수) 들을 답의 ``unread_rows`` 줄로 — 이름이 빈 것은 내 기본 일정함이다.
          - ↑ `holiday_row`
        - `shared_asked` — 곁에 공유 일정함을 청했나 — 이름(``--who``) · 전부(``--shared``)로 청했거나 사람 파일이 고른 일정함이 있다.
        - `people_answer` — 답의 ``people`` — 그 일정함으로 본 분 · 못 본 분 · 사람에게 할 말.
          - `people_word` — 사람 파일로 본 분들의 말 — 못 본 분이 있으면 그 말을 앞에.
            - ↑ `unseen_word`
        - `fit_days` — 보기의 답이 OUT_BYTES 를 넘으면 뒤 날짜의 줄부터 덜어 낸다 — 하루를 가운데서 끊지 않는다(그날이 비어 보이면 그날에 일정을 겹쳐 잡는다). 덜었으면 ``more`` 가 이어 볼 구간을 든다.
        - `again_args` — 덜어 낸 보기를 이어 볼 때 다시 줄 인자 — 공유 · 이름 · 사람 파일.
      - ↑ `fingers`
      - `add_hand` — 새 일정 — 기한이면 알림 자리를 고르고, 판을 짓고, preview 면 판을 내고, 보인 판과 같고 아직 없으면 넣는다.
        - `due_place` — 기한 알림이면 손이 고른 자리를 ``--start`` · ``--end`` 에 적고 어떻게 골랐나를 낸다 — add 가 같은 start · end 로 같은 판을 짓는다.
          - `due_span` — 기한 알림의 (시작, 끝, 어떻게 골랐나). 시각이 있는 기한은 그 시각에 끝나는 ``REMINDER_MINUTES`` 분이다.
            - ↑ `due_of`
            - `due_window` — 기한 날의 알림을 찾을 근무 구간 — 지난 시각은 지금 뒤 첫 눈금부터(``windows_of``). 남은 구간이 알림 길이보다 짧거나 지난 날이면 Stop(인자).
              - ↑ `windows_of`
              - ↑ `hours_of`
              - ↑ `weekday_of`
            - ↑ `busy_spans`
            - ↑ `alongs_of`
            - ↑ `slots_in`
        - `plan_new` — 새 일정 한 건의 판 — (보일 판 · 넣을 것 · 확인에 보인 겹침의 일정 줄). 바꾸지 않는다.
          - ↑ `want_of`
          - ↑ `alongs_of`
          - `new_state` — 새 일정의 판 셈 — (이미 있는 같은 일정이나 None, 이미 선 함께 넣는 건, 겹침의 일정 줄, 겹치는 함께 넣는 건). 이미 있나는 넣을 자리(기본 일정함)에서만 본다.
            - `agenda_changes.already_in` — 읽은 줄 가운데 넣을 것과 같은 일정(``same_event``) — 없으면 None.
              - `agenda_shapes.same_event` — 같은 일정인가 — 제목 · 시작 · 끝이 같다.
                - ↑ `clean_title`
                - ↑ `kst_day`
            - `landed_of` — 함께 넣는 건 가운데 이미 기본 일정함에 선 줄 — 제목 · 시작 · 끝이 같은 것만(``agenda.same_event``). 시각만 겹치는 줄을 여기 넣으면 사람이 못 본 일정이 겹침에서 말없이 빠져 그 위에 넣는다.
              - ↑ `agenda_shapes.same_event`
              - ↑ `agenda_shapes.Want`
          - `new_view` — 새 일정의 보일 판 — 넣을 값 · 이미 있나 · 겹침 · 못 읽은 곁 일정함. 열쇠는 아직 없다.
            - ↑ `agenda_shapes.clock_span`
            - ↑ `weekday_of`
            - ↑ `row`
            - `along_row` — 겹침에 서는 함께 넣는 건 — 일정 줄과 같은 칸에 「planned」.
              - ↑ `weekday_of`
              - ↑ `agenda_shapes.clock_span`
            - ↑ `failed_rows`
          - `keyed` — 보인 판에 열쇠를 단다 — 판 전체(보인 값과 그 둘레)의 해시(``ep_command.fingerprint``). 넣을 판 · 고칠 판이 이것 하나로 단다.
          - `along_word` — 넣을 일정을 다음 건의 ``--alongside`` 꼴 「시작|끝|제목」 으로.
            - ↑ `Along`
        - `shown_changed` — 사람이 본 판과 지금 판이 다른가 — 다시 지은 판의 열쇠(``key``)가 받은 ``--confirm`` 과 다르면 참. 넣기 · 고치기가 이것 하나로 본다.
        - `word_answer` — 끝 낱말과 그 말(``STATE_WORDS``)의 답 — 더 실을 칸은 그 뒤에.
        - `agenda_changes.register` — ⚠ 회사 일정을 바꾼다 — 내 기본 일정함에 한 건을 넣고 ``Added`` 를 낸다.
          - ↑ `values_unfit`
          - ↑ `agenda_shapes.CalendarConfigError`
          - ↑ `agenda_reader.Reader`
          - `_span_of` — 넣을 일정을 앞 · 뒤로 읽을 날 — 하루 종일이면 끝날까지.
            - `_span` — 그 일정을 다시 읽을 날 — 시작하는 날부터 끝나는 날 다음 날까지(앱의 ``end`` 가 그날을 드는지 안 쟀다).
              - ↑ `agenda_shapes.kst_day`
          - ↑ `already_in`
          - `agenda_shapes.Added` — 넣기의 끝 — ``state`` 는 added(다시 읽어 섰다) · already(같은 일정이 이미 있다 · 안 넣었다) · clashed(확인 뒤 그 시각에 새 일정이 들었다 · 안 넣었다) · unsure(넣었는지 모른다).
            - ↑ `Event`
          - `fresh_clash` — 확인 뒤 그 시각에 새로 든 일정의 열쇠(``event_ref``) — 내 일정함 전부(기본 · 곁)에서 겹친 줄 가운데 확인에 안 보인 것.
            - `_side_events` — 기본 밖 내 일정함(Teams 따위)의 ``first`` ~ ``last`` 일정 — 안 읽히는 일정함은 건너뛴다(끊긴 세션은 올린다).
              - ↑ `agenda_reader.read_each`
            - ↑ `agenda_shapes.event_ref`
          - `form_fields` — 보낼 칸 — 폼의 칸을 다 기본값째 싣고 잰 칸만 바꾼다.
            - `agenda_shapes.FormChanged` — 등록 화면의 꼴이 잰 것과 다르다 — 넣지 않았다.
          - `open_form` — 등록 화면의 첫 폼의 칸 — 폼이 없으면 ``SessionExpired``, 잰 칸이 없거나 고정 값이 다르면 ``FormChanged``(둘 다 안 넣는다).
            - `agenda_rows._Form` — 등록 화면의 첫 폼에서 이름 붙은 칸의 값 — 숨은 칸 · 글 칸 · 고른 상자 · 체크된 칸 · 글 상자.
              - `_Form.handle_starttag` — 첫 폼 안의 칸 하나를 적는다 — 보내지 않는 칸(안 고른 체크 · 단추 · 파일)은 빼고, 고르기는 고른 값이나 첫 값을 기다린다.
              - `_Form.handle_endtag` — 폼 · 글 칸 · 고르기가 닫힌다 — 고른 것이 없던 고르기는 첫 값을 갖는다.
              - `_Form.handle_data` — 열린 글 칸(textarea)의 글을 그 칸에 잇는다.
            - ↑ `agenda_shapes.SessionExpired`
            - ↑ `agenda_shapes.FormChanged`
          - `added_after` — 넣은 뒤 다시 읽어 끝을 정한다 — 넣기 앞에 없던 같은 일정이 섰으면 added, 안 섰거나 다시 읽기가 지면 unsure.
            - ↑ `agenda_shapes.CalendarError`
            - ↑ `agenda_shapes.Added`
            - ↑ `agenda_shapes.event_key`
            - ↑ `already_in`
          - `send_form` — 저장 요청 하나 — 도중에 지면 그 예외 이름을 낸다(서버가 받았는지 모른다 · 끝은 다시 읽어 정한다). 다 갔으면 빈 글자.
            - ↑ `agenda_shapes.CalendarError`
        - ↑ `agenda_shapes.event_ref`
        - `ended_answer` — 바꾸는 손의 끝 답 — 낱말 · 그 말 · 지금 그 줄.
          - ↑ `word_answer`
          - ↑ `row`
      - `edit_hand` — 내 일정 한 건 고치기 — 판을 짓고, preview 거나 줄이 바뀌었거나 없으면 판을 내고, 보인 판과 같고 거절이 아니면 고친다.
        - `plan_edit` — 내 일정 한 건을 고칠 판 — 지금 값 · 바뀔 값 · 새 시각의 겹침 · 고칠 수 있나. 바꾸지 않는다.
          - ↑ `agenda_shapes.Seen`
          - `agenda_changes.locate` — 보인 줄을 지금 읽어 — (끝 낱말, 지금 그 줄). 끝 낱말은 ""(그대로) · ``CHANGED``(옮겨졌거나 제목 · 시작 · 끝이 다르다) · ``GONE``(그날에 없다). 고치기 · 지우기와 그 미리 보기가 이것 하나로 본다.
            - ↑ `agenda_shapes.event_ref`
            - ↑ `agenda_shapes.event_ident`
            - ↑ `agenda_shapes.event_mark`
          - `lost_view` — 보인 줄이 바뀌었거나 그날에 없을 때의 판 — 이 명령의 끝 낱말(moved · gone)과 지금 그 줄(없으면 None). 열쇠는 없다.
            - ↑ `row`
          - ↑ `change_of`
          - `row_doc` — 이 줄의 한 건 문서 — 줄에 문서 열쇠가 없으면 None(그 줄은 ``agenda.doc_refusal`` 이 고치지 않는 까닭으로 가른다).
          - `agenda_changes.new_times` — 고친 뒤의 (시작, 끝) — 시작만 주면 길이를 지켜 옮기고(화면의 끌어 옮기기와 같다) 끝만 주면 끝만 바꾼다.
          - ↑ `unfit_stop`
          - ↑ `agenda_changes.values_unfit`
          - `agenda_changes.new_title` — 고친 뒤의 제목 — 안 바꾸면 지금 제목(회사 일정에 남는 꼴).
            - ↑ `agenda_shapes.clean_title`
          - `agenda_changes.row_refusal` — 줄만 보고 가르는 고치지 않는 까닭 — 손수 든 단건이 아니면 그 까닭(``keep_reason``), 하루 종일 줄의 시각을 옮기면 ``KEEP_ALL_DAY``, 아니면 빈 글자. 고칠 판과 고치는 손이 이것 하나로 본다.
          - `agenda_changes.doc_refusal` — 한 건을 보고 가르는 고치지 않는 까닭 — 한 건을 못 읽었으면 ``KEEP_NO_DOC``, 참석자 · 참조자가 들면(모르면 든 것으로) ``KEEP_GUESTS``, 아니면 빈 글자. 고칠 판과 고치는 손이 이것 하나로 본다.
          - `edit_clashes` — 고친 시각에 겹치는 일정 줄(그 일정 자신은 빼고)과 못 읽은 곁 일정함의 (이름, 까닭) — 겹침은 내 일정함 전부에서 본다.
            - ↑ `agenda_shapes.kst_day`
          - ↑ `keyed`
          - `edit_view` — 고칠 판 — 지금 값(``was``) · 바뀔 값(``becomes``) · 새 시각의 겹침 · 거절이면 까닭과 그 말 · 못 읽은 곁 일정함. 열쇠는 아직 없다.
            - ↑ `agenda_shapes.clean_title`
            - ↑ `weekday_of`
            - ↑ `agenda_shapes.kst_day`
            - ↑ `agenda_shapes.clock_span`
            - ↑ `row`
            - ↑ `failed_rows`
        - ↑ `word_answer`
        - ↑ `shown_changed`
        - `agenda_changes.edit` — ⚠ 회사 일정을 바꾼다 — 내 일정함의 한 줄의 제목 · 장소 · 시각을 고친다.
          - ↑ `agenda_shapes.Seen`
          - ↑ `agenda_shapes.ChangeRefused`
          - ↑ `agenda_reader.Reader`
          - ↑ `locate`
          - `agenda_shapes.Edited` — 고치기의 끝 — ``state`` 는 edited(다시 읽어 바꾼 값이 섰다) · gone · changed(보인 뒤 바뀌었다 · 안 고쳤다) · unsure(불렀는데 다시 읽은 값이 바라던 것과 다르다 — ``event`` 가 지금의 그 줄이다).
            - ↑ `Event`
          - ↑ `row_refusal`
          - ↑ `agenda_shapes.CalendarError`
          - ↑ `doc_refusal`
          - ↑ `new_times`
          - `edit_values` — 고친 뒤의 (제목, 장소) — 안 바꾸는 칸은 지금 값.
            - ↑ `new_title`
          - ↑ `values_unfit`
          - ↑ `agenda_shapes.CalendarConfigError`
          - `send_edit` — 고칠 요청 — 제목 · 장소가 바뀌면 미리 보기 [저장], 시각이 바뀌면 끌어 옮기기. (일정 앱이 「참석자께 알릴까」를 물었나, 도중에 진 예외 이름 — 서버가 받았는지 모른다 · 끝은 다시 읽어 정한다).
            - ↑ `agenda_shapes.clean_title`
            - `_agent` — 바꾸는 에이전트 한 번 — GET 에 JSONP 로 답한다.
              - ↑ `agenda_rows._jsonp`
              - ↑ `agenda_shapes.CalendarError`
            - ↑ `agenda_shapes.CalendarError`
          - `edited_after` — 고친 뒤 다시 읽어 끝을 정한다 — 그 일정의 줄과 한 건이 바란 제목 · 장소 · 시각이면 edited, 다르거나 다시 읽기가 지면 unsure.
            - ↑ `agenda_shapes.kst_day`
            - ↑ `agenda_shapes.CalendarError`
            - ↑ `agenda_shapes.Edited`
            - ↑ `agenda_shapes.clean_title`
        - ↑ `agenda_shapes.Seen`
        - ↑ `change_of`
        - ↑ `agenda_shapes.ChangeRefused`
        - `refused_answer` — 바꾸는 손이 거절한 답 — 까닭과 사람에게 할 말.
        - ↑ `ended_answer`
      - `delete_hand` — 내 일정 한 건 지우기 — 손잡이가 곧 열쇠다(보인 줄이 바뀌었으면 손이 안 지운다).
        - `agenda_changes.delete` — ⚠ 회사 일정을 바꾼다 — 내 일정함의 한 줄을 지운다.
          - ↑ `agenda_shapes.Seen`
          - ↑ `agenda_shapes.ChangeRefused`
          - ↑ `agenda_reader.Reader`
          - ↑ `locate`
          - `agenda_shapes.Removed` — 지우기의 끝 — ``state`` 는 deleted(다시 읽어 사라졌다) · gone(그날에 없다 · 안 불렀다) · changed(보인 뒤 바뀌었다 · 안 지웠다 — ``event`` 가 지금의 그 줄이다) · unsure(불렀는데 다시 읽어도 남아 있다 · 지웠는지 모른다).
            - ↑ `Event`
          - `has_guests` — 응답 칸이 찬 내 일정에 참석자 · 참조자가 드나 — 한 건을 읽어 본다.
          - `removed_after` — 지운 뒤 다시 읽어 끝을 정한다 — 그 줄이 사라졌으면 deleted, 남았거나 다시 읽기가 지면 unsure.
            - ↑ `agenda_shapes.CalendarError`
            - ↑ `agenda_shapes.Removed`
            - ↑ `agenda_shapes.event_ref`
          - `send_delete` — 지우기 요청 하나 — 도중에 지면 그 예외 이름을 낸다(서버가 받았는지 모른다 · 끝은 다시 읽어 정한다). 다 갔으면 빈 글자.
            - ↑ `agenda_shapes.CalendarError`
        - ↑ `agenda_shapes.Seen`
        - ↑ `agenda_shapes.ChangeRefused`
        - ↑ `refused_answer`
        - ↑ `ended_answer`
    - ↑ `agenda_shapes.SessionExpired`
    - ↑ `agenda_shapes.SessionMissing`
<!-- /drawn:piece-map -->
